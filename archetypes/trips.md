---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: {{ .Date }}
draft: true
# A bucket key on site-media.oppernik.de (prepare photos with
# tools/media/optimize.py --prefix trips/<trip>). Shown on the card and on top.
# image: trips/<trip>/{{ .File.ContentBaseName }}/cover.jpg
# Uncomment for a post written in German.
# content_language: de
---

The first paragraph doubles as the summary on the card.

{{ "{{<" }} photo src="trips/<trip>/{{ .File.ContentBaseName }}/01.jpg" caption="Caption" >}}

More text.

{{ "{{<" }} photos >}}
{{ "{{<" }} photo src="trips/<trip>/{{ .File.ContentBaseName }}/02.jpg" >}}
{{ "{{<" }} photo src="trips/<trip>/{{ .File.ContentBaseName }}/03.jpg" caption="Caption" >}}
{{ "{{<" }} /photos >}}
