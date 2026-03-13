#!/bin/bash
for f in templates/dashboard/projects/list.html templates/dashboard/roads/list.html templates/dashboard/org_units/list.html templates/dashboard/access/list.html; do
  sed -i 's/<div class="bg-white rounded-2xl shadow-2xl w-full max-w-md" @click.stop>/<form class="bg-white rounded-2xl shadow-2xl w-full max-w-md" @click.stop @submit.prevent="save">/' $f
  sed -i 's/<button @click="save()" :disabled=/<button type="submit" :disabled=/' $f
  # Just in case
  sed -i 's/<\/button>\n      <\/div>\n    <\/div>/<\/button>\n      <\/div>\n    <\/form>/' $f
done
