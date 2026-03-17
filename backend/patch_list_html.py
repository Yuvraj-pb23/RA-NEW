with open("templates/dashboard/roads/list.html", "r") as f:
    content = f.read()

import re

# Remove the detail modal
modal_pattern = r'<!-- Detail Modal -->\s*<div x-show="detailOpen".*?</div>\s*</div>\s*</div>'
content = re.sub(modal_pattern, '', content, flags=re.DOTALL)

with open("templates/dashboard/roads/list.html", "w") as f:
    f.write(content)
