# Operator convenience targets for the OT reference lab's Docker host
# (OT-HOST01). Manual use only -- the OT team runs these by hand when
# needed (e.g. a stalled simulation). Never invoked by NinjaOne or any
# automation: D-1/D-2 keep NinjaOne software and any NinjaOne-triggered
# action off this host and off the PLCs. See CLAUDE.md hard rule 2 --
# this does not touch the ST programs, only the container lifecycle.
#
# Usage: make -f ot-host.mk <target>

.PHONY: help status logs-plc01 logs-plc02 stop-plc01 stop-plc02 \
        start-plc01 start-plc02 restart-plc01 restart-plc02 restart-all

help:
	@echo "Targets:"
	@echo "  status         - container status + live resource stats"
	@echo "  logs-plc01     - tail plc01 container logs"
	@echo "  logs-plc02     - tail plc02 container logs"
	@echo "  stop-plc01     - stop plc01"
	@echo "  stop-plc02     - stop plc02"
	@echo "  start-plc01    - start plc01"
	@echo "  start-plc02    - start plc02"
	@echo "  restart-plc01  - restart plc01 (e.g. if its state looks stuck)"
	@echo "  restart-plc02  - restart plc02"
	@echo "  restart-all    - restart both"

status:
	docker ps --format '{{.Names}}\t{{.Status}}'
	@echo
	docker stats --no-stream plc01 plc02

logs-plc01:
	docker logs --tail 100 -f plc01

logs-plc02:
	docker logs --tail 100 -f plc02

stop-plc01:
	docker stop plc01

stop-plc02:
	docker stop plc02

start-plc01:
	docker start plc01

start-plc02:
	docker start plc02

restart-plc01:
	docker restart plc01

restart-plc02:
	docker restart plc02

restart-all: restart-plc01 restart-plc02
	@echo "Both PLC containers restarted."
