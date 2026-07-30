PYTHON := /Users/lc/.workbuddy/binaries/python/versions/3.13.12/bin/python3
VENV := server/.venv
NODE_BIN := /Users/lc/.workbuddy/binaries/node/versions/22.22.2/bin

.PHONY: setup server web build check clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -r server/requirements.txt
	@[ -f server/.env ] || cp server/.env.example server/.env
	cd web && PATH="$(NODE_BIN):$$PATH" npm install --no-audit --no-fund
	@echo "初始化完成，记得填写 server/.env 里的 SUBSONIC__* 配置"

server:
	cd server && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd web && PATH="$(NODE_BIN):$$PATH" npm run dev

build:
	cd web && PATH="$(NODE_BIN):$$PATH" npm run build

check:
	cd web && PATH="$(NODE_BIN):$$PATH" npx tsc -b
	$(VENV)/bin/python -c "from app.main import create_app; create_app(); print('server ok')" 2>/dev/null || \
		(cd server && .venv/bin/python -c "from app.main import create_app; create_app(); print('server ok')")

clean:
	rm -rf $(VENV) web/node_modules web/dist
