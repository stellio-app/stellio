"""v1.0.7 — garde-fous serveur / LXC : surveillance, limites, journaux, script d'installation robuste."""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = open(os.path.join(ROOT, 'install-pi.sh'), encoding='utf-8').read()


def test_install_script_syntax_and_single_block():
    assert subprocess.run(['bash', '-n', os.path.join(ROOT, 'install-pi.sh')]).returncode == 0
    # tout le script est dans un bloc { ... } : la mise a jour du depot en cours d'execution ne peut pas le corrompre
    body = SH.split('{\n', 1)[1] if '\n{\n' in SH else ''
    assert '\n{\nbold "=== Installation' in SH
    assert SH.rstrip().endswith('exit 0\n}')


def test_service_never_gives_up_and_guard_dropin():
    assert 'StartLimitIntervalSec=0' in SH
    for key in ('OOMScoreAdjust=300', 'TasksMax=512', 'LimitNOFILE=8192', 'TimeoutStopSec=20'):
        assert key in SH
    # on n'ecrase jamais les plafonds poses par le script LXC
    assert 'if [ ! -f "$LIMITS_FILE" ]' in SH
    assert 'MemoryMax=$((MEM_MB * 85 / 100))M' in SH and 'MemoryHigh=$((MEM_MB * 75 / 100))M' in SH


def test_journal_capped_and_timer():
    assert 'SystemMaxUse=100M' in SH and 'MaxRetentionSec=2week' in SH
    assert 'OnUnitActiveSec=1min' in SH and 'enable --now stellio-watchdog.timer' in SH


def _watchdog(tmp_path, ip='10.0.0.2', active=True, age=500, ping=True, free=5000, times=1):
    m = re.search(r"tee /usr/local/bin/stellio-watchdog > /dev/null <<'EOF' \|\| GUARD_OK=false\n(.*?)\nEOF\n", SH, re.S)
    script = m.group(1)
    state, log, binp = tmp_path / 'state', tmp_path / 'calls', tmp_path / 'bin'
    binp.mkdir(exist_ok=True)
    script = script.replace('/run/stellio-watchdog', str(state)).replace('/etc/default/stellio-watchdog', str(tmp_path / 'n1')).replace('/etc/stellio-lxc.conf', str(tmp_path / 'n2'))
    (tmp_path / 'wd').write_text(script)
    log.write_text('')

    def fake(name, body):
        p = binp / name
        p.write_text('#!/bin/bash\n' + body + '\n')
        p.chmod(0o755)
    fake('logger', 'echo "LOG $*" >> %s' % log)
    fake('hostname', 'echo "%s"' % ip)
    fake('systemctl', 'case "$1" in is-active) exit %d;; show) echo 123;; *) echo "SYSTEMCTL $*" >> %s;; esac' % (0 if active else 1, log))
    fake('ps', 'echo " %d"' % age)
    fake('curl', 'exit %d' % (0 if ping else 22))
    fake('df', 'echo hdr; echo "x 1 1 %d 1 /"' % free)
    fake('journalctl', 'echo "JOURNAL $*" >> %s' % log)
    fake('apt-get', 'echo "APT $*" >> %s' % log)
    env = dict(os.environ, PATH=str(binp) + ':' + os.environ['PATH'])
    for _ in range(times):
        subprocess.run(['bash', str(tmp_path / 'wd')], env=env, check=True)
    return log.read_text()


def test_watchdog_restarts_after_three_failed_pings(tmp_path):
    assert 'SYSTEMCTL restart' not in _watchdog(tmp_path, ping=False, times=2)
    assert 'SYSTEMCTL restart stellio' in _watchdog(tmp_path, ping=False, times=1)


def test_watchdog_grace_period_after_start(tmp_path):
    assert 'restart' not in _watchdog(tmp_path, ping=False, age=30, times=5)


def test_watchdog_starts_stopped_service(tmp_path):
    r = _watchdog(tmp_path, active=False)
    assert 'reset-failed' in r and 'SYSTEMCTL start stellio' in r


def test_watchdog_frees_disk_and_restarts_network(tmp_path):
    r = _watchdog(tmp_path, free=100)
    assert 'JOURNAL --vacuum-size=20M' in r and 'APT clean' in r
    r = _watchdog(tmp_path, ip='', times=2)
    assert 'restart systemd-networkd' in r
