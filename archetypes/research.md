---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: {{ .Date }}
draft: true
# Tags drive the filter on /research/; posts about the thesis carry `thesis`.
tags: []
# Optional. A bucket key (research/<post>/cover.jpg on site-media.oppernik.de)
# or a file under static/ (/uploads/…). Shown on the card and above the post.
# image: research/{{ .File.ContentBaseName }}/cover.jpg
---

The first paragraph doubles as the summary on the card — make it say what the post is about.

## A heading

Text. A photo from the bucket, with a caption:

{{ "{{<" }} photo src="research/{{ .File.ContentBaseName }}/figure-1.jpg" caption="What the figure shows" >}}
