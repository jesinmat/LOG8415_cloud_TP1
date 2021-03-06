#!/usr/bin/bash

git clone https://github.com/jesinmat/LOG8415_cloud_TP1.git && cd LOG8415_cloud_TP1

python3 - <<'END_SCRIPT'

import subprocess
import os
import time
from load_balancer import AmazonManager

manager = AmazonManager()
manager.setup()

time.sleep(2*60)

completed = subprocess.run(["bash", "-c",
f"""#!/usr/bin/bash
cd docker-loadtester &&
./buildDockerImage.sh &&

export AWS_URL='http://{manager.dns_name}' &&
./runDockerContainer.sh
"""])

manager.shutdown()

END_SCRIPT
