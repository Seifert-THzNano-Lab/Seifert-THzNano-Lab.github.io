---
title: Papers
nav:
  order: 2
  tooltip: Published works
---

# {% include icon.html icon="fa-solid fa-microscope" %} Papers

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
/* Highlight Grid Styles */
.custom-grid-container { display: flex; flex-wrap: wrap; margin: 0 -10px; }
.custom-grid-item { width: 33.333%; padding: 0 10px; box-sizing: border-box; }
@media (max-width: 768px) { .custom-grid-item { width: 100%; } }
.dim-on-hover:hover .research-card { opacity: 0.4; filter: grayscale(100%); }
.dim-on-hover .research-card:hover { opacity: 1 !important; filter: none !important; }

/* Year Index Navigation Bar */
.year-index-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  justify-content: center;
  position: relative;
  z-index: 20; 
}

/* Specific styling for bottom nav */
.year-index-nav.bottom-nav {
  margin-top: 40px; /* Space between content and bottom nav */
  margin-bottom: 20px;
  background: #f8f9fa; /* Match top nav background */
  border-top: 1px solid #e0e0e0;
}

.year-btn {
  cursor: pointer;
  background-color: #fff;
  border: 1px solid #ced4da;
  color: #495057;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
  user-select: none;
}
.year-btn:hover {
  background-color: #e2e6ea;
  border-color: #adb5bd;
}
.year-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
  box-shadow: 0 2px 4px rgba(0,123,255,0.3);
}
.year-btn .count {
  font-size: 0.8em;
  margin-left: 5px;
  opacity: 0.7;
}

/* Year Cards */
.year-card {
  display: none; /* Hide by default */
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 1rem; 
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  background-color: #fff;
  animation: fadeIn 0.4s ease-in-out;
  /* CRITICAL: Must be visible for sticky children to work */
  overflow: visible !important; 
}

.year-card.active-year {
  display: block;
  border: 1px solid #007bff; 
  box-shadow: 0 0 10px rgba(0,123,255,0.1);
}

/* STICKY HEADER SETUP */
.year-header {
  background-color: #f1f3f5;
  padding: 12px 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  /* POSITIONING */
  position: -webkit-sticky; /* For Safari */
  position: sticky;
  
  /* OFFSET: 70px to clear the main navbar. Adjust if needed. */
  top: 70px; 
  
  z-index: 900; 
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.year-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
  border-bottom: none;
  padding-bottom: 0;
}
.year-content { padding: 0 20px; }

/* Separator between papers */
.year-content > div { border-bottom: 1px solid #eee; padding: 10px 0; }
.year-content > div:last-child { border-bottom: none; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

{% include section.html %}

## All Publications

{% assign papers_by_year = site.data.citations | group_by_exp: "item", "item.date | date: '%Y' | default: item.year" %}
{% assign sorted_years = papers_by_year | sort: 'name' | reverse %}

<div id="top-nav-anchor" class="year-index-nav">
{% for year_group in sorted_years %}
  {% if year_group.name != "" %}
  <div 
    class="year-btn" 
    onclick="selectYear('{{ year_group.name }}', false)"
    data-year="{{ year_group.name }}">
    {{ year_group.name }}
    <span class="count">{{ year_group.items | size }}</span>
  </div>
  {% endif %}
{% endfor %}
</div>

{% include search-box.html %}
{% include search-info.html %}

{% for year_group in sorted_years %}
{% if year_group.name != "" %}
<div id="content-{{ year_group.name }}" class="year-card">
  
  <div class="year-header">
    <h2>{{ year_group.name }}</h2>
  </div>
  
  <div class="year-content">
    {% for item in year_group.items %}
    <div>
      {% include citation.html lookup=item.id style="rich" %}
    </div>
    {% endfor %}
  </div>

</div>
{% endif %}
{% endfor %}

<div class="year-index-nav bottom-nav">
{% for year_group in sorted_years %}
  {% if year_group.name != "" %}
  <div 
    class="year-btn" 
    onclick="selectYear('{{ year_group.name }}', true)"
    data-year="{{ year_group.name }}">
    {{ year_group.name }}
    <span class="count">{{ year_group.items | size }}</span>
  </div>
  {% endif %}
{% endfor %}
</div>

<script>
/**
 * Selects a year to display.
 * @param {string} year - The year to show (e.g., '2023')
 * @param {boolean} fromBottom - If true, scroll back to top of the list for better UX
 */
function selectYear(year, fromBottom) {
  // 1. Hide all content cards
  var cards = document.getElementsByClassName('year-card');
  for (var i = 0; i < cards.length; i++) {
    cards[i].classList.remove('active-year');
  }

  // 2. Deactivate all buttons (Top and Bottom)
  var btns = document.getElementsByClassName('year-btn');
  for (var i = 0; i < btns.length; i++) {
    btns[i].classList.remove('active');
  }

  // 3. Show the selected content
  var selectedContent = document.getElementById('content-' + year);
  if (selectedContent) selectedContent.classList.add('active-year');

  // 4. Activate the buttons for this year (Selects both Top and Bottom buttons)
  var activeBtns = document.querySelectorAll('.year-btn[data-year="' + year + '"]');
  for (var i = 0; i < activeBtns.length; i++) {
    activeBtns[i].classList.add('active');
  }

  // 5. Optional UX: If clicked from bottom, scroll back to top nav so user sees the new list
  if (fromBottom) {
     var anchor = document.getElementById('top-nav-anchor');
     if(anchor) anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Initialize: Click the first button (Newest Year) automatically on load
document.addEventListener('DOMContentLoaded', function() {
  // Find the first button in the top navigation
  var firstBtn = document.querySelector('.year-index-nav .year-btn');
  if (firstBtn) {
    var year = firstBtn.getAttribute('data-year');
    selectYear(year, false);
  }
});
</script>