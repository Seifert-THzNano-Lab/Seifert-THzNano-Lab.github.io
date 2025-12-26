---
title: Research
nav:
  order: 1
  tooltip: Published works
---

# {% include icon.html icon="fa-solid fa-microscope" %}Research

We develop and use novel approaches for terahertz time-domain spectroscopy capable of combining femtosecond temporal and nanometer spatial resolutions. 
These steps are key to explore ultrafast dynamics in complex nanomaterials on the spatiotemporal scales relevant for applications and fundamental insights.

{% include section.html %}


## Highlighted

<div class="custom-grid-container dim-on-hover">
  {% for item in site.data.research_highlights %}
    <div class="custom-grid-item">
      {% include feature_research.html 
        image=item.image 
        title=item.title 
        journal=item.journal 
        authors=item.authors 
        abstract=item.abstract 
        link=item.link 
      %}
    </div>
  {% endfor %}
</div>

<style>
  .custom-grid-container {
      display: flex;
      flex-wrap: wrap;
      margin-left: -10px;
      margin-right: -10px;
  }
  .custom-grid-item {
      width: 33.333%;
      padding: 0 10px;
      box-sizing: border-box;
  }
  @media (max-width: 768px) {
      .custom-grid-item { width: 100%; }
  }
  .dim-on-hover:hover .research-card {
      opacity: 0.4;
      filter: grayscale(100%);
  }
  .dim-on-hover .research-card:hover {
      opacity: 1 !important;
      filter: none !important;
  }
</style>

{% include section.html %}

## All

{% include search-box.html %}

{% include search-info.html %}

{% include list.html data="citations" component="citation" style="rich" %}