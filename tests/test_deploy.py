from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    return (ROOT / "deploy" / name).read_text()


def test_unit_starts_the_same_app_as_the_procfile():
    app = "career_platform.main:app --app-dir src"
    assert app in (ROOT / "Procfile").read_text()
    assert app in read("career-platform.service")


def test_unit_listens_only_on_localhost_port_8000():
    unit = read("career-platform.service")
    assert "--host 127.0.0.1" in unit and "--port 8000" in unit
    assert "0.0.0.0" not in unit


def test_unit_restarts_runs_as_career_and_reads_the_env_file():
    unit = read("career-platform.service")
    for line in (
        "Restart=always",
        "User=career",
        "WorkingDirectory=/opt/career-platform",
        "EnvironmentFile=/etc/career-platform/env",
        "WantedBy=multi-user.target",
    ):
        assert line in unit


def test_nginx_proxies_to_the_unit_port():
    assert "proxy_pass http://127.0.0.1:8000;" in read("nginx-career-platform.conf")


def test_nginx_serves_https_with_the_cloudflare_origin_certificate():
    conf = read("nginx-career-platform.conf")
    for line in (
        "listen 443 ssl;",
        "server_name chelseahuang.me www.chelseahuang.me aws.chelseahuang.me;",
        "ssl_certificate     /etc/ssl/cloudflare/origin.pem;",
        "ssl_certificate_key /etc/ssl/cloudflare/origin.key;",
    ):
        assert line in conf


def test_nginx_passes_the_original_host_and_scheme():
    conf = read("nginx-career-platform.conf")
    assert "proxy_set_header Host $host;" in conf
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in conf
