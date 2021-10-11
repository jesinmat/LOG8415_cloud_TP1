#!/usr/bin/bash

git clone git@github.com:jesinmat/LOG8415_cloud_TP1.git && cd LOG8415_cloud_TP1
git checkout pierre

python3 - <<'END_SCRIPT'

import subprocess
import os
from load_balancer import AmazonManager

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
