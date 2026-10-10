---
title: "{{ replace .File.ContentBaseName "-" " " | title }}"
date: {{ .Date }}
draft: true
# One sentence for the project card on /projects/.
summary: TODO
# A bucket key on site-media.oppernik.de, for the card.
image: projects/{{ .File.ContentBaseName }}/cover.jpg
tags: []
---

{{ "{{<" }} breadcrumbs >}}

# {{ replace .File.ContentBaseName "-" " " | title }}

TODO: the pitch — what it is and why you built it, in two or three sentences.

[Code on GitHub](https://github.com/nikkeop/TODO){:.button} [Write-up](#how-it-works){:.button.ghost}

![](projects/{{ .File.ContentBaseName }}/cover.jpg)

---

## The problem

TODO: what was missing, broken or interesting.

![](projects/{{ .File.ContentBaseName }}/detail-1.jpg){:.float}

---

## How it works

TODO: the approach, the hardware or the stack, what was hard.

![](projects/{{ .File.ContentBaseName }}/detail-2.jpg){:.float}

---

## Facts

- **Status:** TODO (idea, in progress, done)
- **Built with:** TODO
- **Time:** TODO

---

## Gallery

{{ "{{<" }} photos >}}
{{ "{{<" }} photo src="projects/{{ .File.ContentBaseName }}/03.jpg" caption="Caption" >}}
{{ "{{<" }} photo src="projects/{{ .File.ContentBaseName }}/04.jpg" caption="Caption" >}}
{{ "{{<" }} /photos >}}

---.cta
