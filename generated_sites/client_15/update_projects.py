import re

with open('projects.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Filters
old_filters = '''<div class="project-filters">
            <button class="filter-btn active">All Projects</button>
            <button class="filter-btn">Modern Block</button>
            <button class="filter-btn">Family Homes</button>
            <button class="filter-btn">Energy Efficient</button>
        </div>'''

new_filters = '''<div class="project-filters">
            <button class="filter-btn active" data-filter="all">All Projects</button>
            <button class="filter-btn" data-filter="modern-block">Modern Block</button>
            <button class="filter-btn" data-filter="family-homes">Family Homes</button>
            <button class="filter-btn" data-filter="energy-efficient">Energy Efficient</button>
        </div>'''
        
content = content.replace(old_filters, new_filters)

# 2. Add CSS
css = '''
        /* Card Carousel Styles */
        .project-card .img-wrapper {
            position: relative;
            display: flex;
        }
        .card-carousel-track {
            display: flex;
            width: 100%;
            height: 100%;
            transition: transform 0.4s ease;
        }
        .card-carousel-track img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            flex-shrink: 0;
        }
        .card-carousel-btn {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(0,0,0,0.4);
            color: #fff;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition);
            opacity: 0;
        }
        .project-card .img-wrapper:hover .card-carousel-btn {
            opacity: 1;
        }
        .card-carousel-btn:hover { background: rgba(0,0,0,0.8); }
        .card-carousel-btn.prev { left: 0.5rem; }
        .card-carousel-btn.next { right: 0.5rem; }
        .card-carousel-btn svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2; }
'''
if '.card-carousel-track' not in content:
    content = content.replace('</style>', css + '\n</style>')

# 3. Process each article
# categories based on current title/h4
categories = {
    'The Kaliningrad Block': 'modern-block',
    'Petersburg Haven': 'family-homes',
    'Eco-Villa Orenburg': 'energy-efficient',
    'Nordic Minimalist Retreat': 'modern-block',
    'The Concrete Manor': 'family-homes',
    'Alpine A-Frame Concept': 'energy-efficient'
}

articles = re.findall(r'(<article class="project-card">.*?<\/article>)', content, re.DOTALL)
for act in articles:
    # identify category
    cat = 'modern-block'
    for k, v in categories.items():
        if k in act:
            cat = v
            break
            
    # extract original img
    img_match = re.search(r'(<img [^>]+>)', act)
    orig_img = img_match.group(1) if img_match else ''
    
    # ensure closing tag for img if absent
    if not orig_img.endswith('/>') and orig_img.endswith('>'):
        orig_img = orig_img[:-1] + ' />'
        
    imgs = [
        orig_img,
        '<img src="https://images.unsplash.com/photo-1628624747186-a941c476b7ef?auto=format&fit=crop&w=600&q=80" alt="Interior view" loading="lazy" />',
        '<img src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80" alt="Outdoor view" loading="lazy" />'
    ]
    
    # replacement img-wrapper block
    # original block has <div class="img-wrapper"> \n <span class="status-badge">...</span> \n <img ...> \n </div>
    # we want to leave the span inside img-wrapper, and replace the img with the track + buttons.
    status_match = re.search(r'(<span class="status-badge">.*?</span>)', act)
    status_html = status_match.group(1) if status_match else ''
    
    track_html = '<div class="card-carousel-track">' + "".join(imgs) + '</div>'
    btns_html = '''
                        <button class="card-carousel-btn prev" aria-label="Previous image">
                            <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"></path></svg>
                        </button>
                        <button class="card-carousel-btn next" aria-label="Next image">
                            <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"></path></svg>
                        </button>
    '''
    
    new_wrapper = f'<div class="img-wrapper">\n{status_html}\n{track_html}\n{btns_html}\n</div>'
    
    # replace old img-wrapper completely
    old_wrapper = re.search(r'<div class="img-wrapper">.*?</div>', act, re.DOTALL).group(0)
    
    new_act = act.replace(old_wrapper, new_wrapper)
    new_act = new_act.replace('<article class="project-card">', f'<article class="project-card" data-category="{cat}">')
    
    content = content.replace(act, new_act)

# 4. JS Script Update 
js_addition = '''
            // Filtering Logic
            const filterBtns = document.querySelectorAll('.filter-btn');
            const projectCards = document.querySelectorAll('.project-card');

            filterBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    filterBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    const filter = btn.getAttribute('data-filter');
                    
                    projectCards.forEach(card => {
                        if (filter === 'all' || card.getAttribute('data-category') === filter) {
                            card.style.display = 'block';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                });
            });

            // Card Carousel Logic
            const cards = document.querySelectorAll('.project-card');
            cards.forEach(card => {
                const track = card.querySelector('.card-carousel-track');
                const prevBtn = card.querySelector('.card-carousel-btn.prev');
                const nextBtn = card.querySelector('.card-carousel-btn.next');
                
                if (track && prevBtn && nextBtn) {
                    const images = track.querySelectorAll('img');
                    let currentIndex = 0;
                    
                    const handleArrowClick = (e, direction) => {
                        e.preventDefault(); 
                        e.stopPropagation();
                        
                        if (direction === 'prev') {
                            currentIndex = (currentIndex > 0) ? currentIndex - 1 : images.length - 1;
                        } else {
                            currentIndex = (currentIndex < images.length - 1) ? currentIndex + 1 : 0;
                        }
                        track.style.transform = 	ranslateX(-%);
                    };

                    prevBtn.addEventListener('click', (e) => handleArrowClick(e, 'prev'));
                    nextBtn.addEventListener('click', (e) => handleArrowClick(e, 'next'));
                }
            });
'''

js_target = '            }\n        });\n    </script>'
if 'Filtering Logic' not in content:
    new_js = '            }\n' + js_addition + '        });\n    </script>'
    content = content.replace(js_target, new_js)

with open('projects.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("projects.html JS and UI actionability updated!")
