# collector agent

## sudo vim /etc/systemd/system/zbx_agent.service
[Unit]
Description=zbx_agent_python
After=network.target

[Service]
Type=simple
ExecStart=`script.py` > /dev/null 2>&1 &
Restart=always

[Install]
WantedBy=multi-user.target

## sudo systemctl daemon-reload
## sudo systemctl enable zbx_agent.service
## sudo systemctl start zbx_agent.service

