---
title: Focus
nav:
  order: 1
  tooltip: Research directions
 
---

# {% include icon.html icon="fa-solid fa-wrench" %}Focus

Our three focus areas describe promising ongoing projects that we plan to further expand in the future.


<div class="lab-grid">
  {% assign featured_projects = site.data.projects | where: "group", "featured" %}
  {% for project in featured_projects %}
    <div class="lab-card">
      <div class="lab-card-image">
        <img src="{{ project.image | relative_url }}" alt="{{ project.title }}">
      </div>
      <div class="lab-card-content">
        <h3 class="lab-card-title">{{ project.title }}</h3>
        <div class="lab-card-text">
          {{ project.description | markdownify }}
        </div>
      </div>
    </div>
  {% endfor %}
</div>

<style>
/* 1. Grid Container */
.lab-grid {
  display: grid;
  /* Fit 3 cards; wraps if screen is too small */
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin-top: 40px;
  padding: 20px; /* Padding allows space for the zoom effect without clipping */
}

/* 2. The Card (Base State) */
.lab-card {
  position: relative;
  height: 480px; /* Fixed height for uniformity */
  background: #ffffff;
  border: 1px solid #e1e4e8;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden; 
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  
  /* CRITICAL: Smooth transition for the scaling effect */
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  transform-origin: center center; /* Zoom from the middle */
  z-index: 1;
}

/* --- THE FOCUS EFFECT --- */

/* Step A: When hovering the GRID, dim all cards */
.lab-grid:hover .lab-card {
  opacity: 0.4;
  filter: grayscale(100%); /* Turn non-selected projects black & white */
  transform: scale(0.95);  /* Shrink them slightly to emphasize the active one */
}

/* Step B: When hovering a SPECIFIC CARD, highlight it */
.lab-card:hover {
  opacity: 1 !important;    /* Force full visibility */
  filter: grayscale(0%) !important; /* Force full color */
  z-index: 100;             /* Bring to the very front */
  
  /* THIS IS THE KEY CHANGE: */
  /* Scale width AND height proportionally */
  transform: scale(1.15) !important; 
  
  box-shadow: 0 25px 50px rgba(0,0,0,0.25); /* Strong shadow to show depth */
  border-color: #0366d6;
}

/* 3. Image Section */
.lab-card-image {
  height: 50%; /* Image always takes top 50% */
  width: 100%;
  background-color: #f8f9fa;
  border-bottom: 1px solid #eaecef;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.lab-card-image img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain; /* Ensures the whole plot fits */
}

/* 4. Text Section */
.lab-card-content {
  height: 50%; /* Text always takes bottom 50% */
  padding: 20px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

.lab-card-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #24292e;
  margin-top: 0;
  margin-bottom: 10px;
}

.lab-card-text {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #586069;
  
  /* Scrollbar logic for long text */
  flex-grow: 1;
  overflow-y: auto; 
  padding-right: 5px; 
  scrollbar-width: thin;
}

/* Scrollbar styling */
.lab-card-text::-webkit-scrollbar {
  width: 4px;
}
.lab-card-text::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 4px;
}
.lab-card-text a {
  color: #0366d6;
  text-decoration: none;
}
</style>