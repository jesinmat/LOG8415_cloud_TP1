#!/usr/bin/bash

git clone git@github.com:jesinmat/LOG8415_cloud_TP1.git && cd LOG8415_cloud_TP1

python3 - <<'END_SCRIPT'

import subprocess
from load_balancer import manager

manager = AmazonManager()
manager.setup()

subprocess.run(f"""#!/usr/bin/bash
cd docker-loadtester
./buildDockerImage.sh

export AWS_URL='http://{manager.dns_name}'
./runDockerContainer.sh
""")

manager.shutdown()

END_SCRIPT
