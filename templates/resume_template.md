\# {{name}}

{{title}}



📧 {{email}} | 📍 {{location}}



\---



\## Skills

{{skills}}



\---



\## Experience



{% for exp in experience %}

\### {{exp.role}} — {{exp.company}}

{{exp.dates}}



{% for b in exp.bullets %}

\- {{b}}

{% endfor %}



{% endfor %}



\---



\## Projects



{% for p in projects %}

\### {{p.name}}



{% for b in p.bullets %}

\- {{b}}

{% endfor %}



{% endfor %}

