---

title: Team

nav:

  order: 3

  tooltip: About our team

---



# {% include icon.html icon="fa-solid fa-users" %}Team



Our international team includes researcher at a variety of academic stages, ranging from master students, via PhD candidates to postdoctoral researchers.



{% include section.html %}



{% include list.html data="members" component="portrait" filter="role == 'pi'" %}
{% include list.html data="members" component="portrait" filter="role != 'pi' and group != 'alum'" %}

{% include section.html %}

## {% include icon.html icon="fa-solid fa-graduation-cap" %}Alumni

{% include list.html data="members" component="portrait" filter="group == 'alum'" style="small" %}