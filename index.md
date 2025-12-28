---
---

<style>
  /* 1. Main Container: Flexbox to put Vision Left, News Right */
  .home-split-container {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    gap: 60px; /* Generous space between text and news */
    margin-bottom: 30px;
    align-items: flex-start;
  }

  /* 2. Research Vision (Left) - Takes more space (65%) */
  .intro-text-box {
    flex: 1; /* Grow to fill space */
  }
  
  /* Make the Vision Title dominant */
  .intro-text-box h1 {
    margin-top: 0;
    font-size: 2.2rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #222;
  }
  
  .intro-text-box p.lead {
    font-size: 1.1rem;
    line-height: 1.6;
    color: #444;
  }

  /* 3. News Sidebar (Right) - Fixed width (30%), subtle design */
  .news-sidebar-clean {
    flex: 0 0 280px; /* Fixed width */
    /* No background color, just a clean left border line */
    border-left: 2px solid #eee; 
    padding-left: 25px; 
    margin-top: 10px; /* Slight offset to align with text */
  }

  /* News Styling */
  .news-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #999;
    font-weight: 700;
    margin-bottom: 15px;
    display: block;
  }

  .news-item {
    margin-bottom: 20px;
  }

  .news-date {
    font-size: 0.75rem;
    color: #888;
    margin-bottom: 2px;
  }

  .news-link {
    font-size: 0.95rem;
    font-weight: 600;
    color: #333;
    text-decoration: none;
    line-height: 1.3;
    display: block;
  }

  .news-link:hover {
    color: #0056b3; /* Standard blue on hover */
  }

  /* MOBILE: Stack them vertically */
  @media (max-width: 850px) {
    .home-split-container {
      flex-direction: column; /* Vision top, News bottom */
      gap: 40px;
    }
    .news-sidebar-clean {
      width: 100%;
      border-left: none; /* Remove side border */
      border-top: 2px solid #eee; /* Add top border */
      padding-left: 0;
      padding-top: 25px;
      margin-top: 0;
    }
  }
</style>

<div class="home-split-container">
  
  <div class="intro-text-box">
    <h2>Our research vision</h2>
    <p class="lead">
      We explore the ultrafast dynamics of spins and magnetism, harnessing terahertz fields to control quantum magnets at the nanoscale. Our research pushes the boundaries of spin‑orbitronics, turning femtosecond and nanometer phenomena into future applications.
    </p>
  </div>

  <div class="news-sidebar-clean">
    <span class="news-label">Latest News</span>
    
    {% for post in site.posts limit:3 %}
      <div class="news-item">
        <div class="news-date">{{ post.date | date: "%B %Y" }}</div>
        <a href="{{ post.url | relative_url }}" class="news-link">
          {{ post.title }}
        </a>
      </div>
    {% endfor %}
    
    {% if site.posts.size == 0 %}
      <p style="font-size:0.8rem; color:#999;">No news updates yet.</p>
    {% endif %}

    <a href="{{ '/news/' | relative_url }}" style="font-size: 0.85rem; color: #666; text-decoration: underline;">
      All updates &rarr;
    </a>
  </div>

</div>

{% include section.html %}

## Highlights

{% capture text %}

We develop and use novel approaches for terahertz time-domain spectroscopy capable of combing femtosecond temporal and nanometer spatial resolutions. These steps are key to explore ultrafast dynamics in complex nanomaterials on the spatiotemporal scales relevant for applications and fundamental insights.

{%
  include button.html
  link="research"
  text="See our publications"
  icon="fa-solid fa-arrow-right"
  flip=true
  style="bare"
%}

{% endcapture %}

{%
  include feature.html
  image="images/NATS_scheme.svg"
  link="research"
  title="Our Research"
  text=text
%}

{% capture text %}

We focus on magnetic materials and aim at gaining control over the ultrafast dynamics of the order parameter on nanoscales. Promising research directions include terahertz dynamics in multiferroics or 2D materials.

{%
  include button.html
  link="projects"
  text="Browse our focus projects"
  icon="fa-solid fa-arrow-right"
  flip=true
  style="bare"
%}

{% endcapture %}

{%
  include feature.html
  image="images/projects.jpg"
  link="projects"
  title="Our Projects"
  flip=true
  style="bare"
  text=text
%}

{% capture text %}

Our international team includes researcher at a variety of academic stages, ranging from master students, via PhD candidates to postdoctoral researchers.

{%
  include button.html
  link="team"
  text="Meet our team"
  icon="fa-solid fa-arrow-right"
  flip=true
  style="bare"
%}

{% endcapture %}

{%
  include feature.html
  image="images/groupphoto.jpeg"
  link="team"
  title="Our Team"
  text=text
%}