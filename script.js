/* Shared enhancement: every page stays readable without JavaScript. */
(() => {
  'use strict';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const header = document.querySelector('header');
  const main = document.querySelector('main');
  const nav = document.querySelector('header .nav, header .tabs');
  document.documentElement.classList.add('js');
  const make = (tag, className) => { const el = document.createElement(tag); el.className = className; return el; };
  if (main) {
    main.id ||= 'main-content';
    const skip = make('a', 'skip-link'); skip.href = '#' + main.id; skip.textContent = 'İçeriğe geç'; document.body.prepend(skip);
    main.classList.add('page-enter');
  }
  const ambient = make('div', 'ambient'); ambient.setAttribute('aria-hidden', 'true');
  ambient.append(make('span', 'orb'), make('span', 'orb')); document.body.prepend(ambient);
  const progress = make('div', 'reading-progress'); progress.setAttribute('aria-hidden', 'true'); document.body.prepend(progress);
  const topButton = make('button', 'to-top'); topButton.type = 'button'; topButton.textContent = '↑'; topButton.setAttribute('aria-label', 'Sayfanın başına dön'); topButton.tabIndex = -1; document.body.append(topButton);
  topButton.addEventListener('click', () => { window.scrollTo({top:0, behavior:reduce.matches ? 'instant' : 'smooth'}); document.querySelector('header a')?.focus({preventScroll:true}); });
  let menu;
  const closeMenu = () => { nav?.classList.remove('menu-open'); menu?.setAttribute('aria-expanded', 'false'); if(menu) menu.textContent='Menü ☰'; };
  if (nav && header) {
    nav.id ||= 'site-navigation';
    menu = make('button','menu-toggle'); menu.type='button'; menu.textContent='Menü ☰'; menu.setAttribute('aria-expanded','false'); menu.setAttribute('aria-controls',nav.id); menu.setAttribute('aria-label','Ana menüyü aç veya kapat');
    (header.querySelector('.head, .headrow') || header.querySelector('.wrap') || header).append(menu);
    menu.addEventListener('click', () => { const open=menu.getAttribute('aria-expanded')!=='true'; nav.classList.toggle('menu-open',open); menu.setAttribute('aria-expanded',String(open)); menu.textContent=open?'Kapat ×':'Menü ☰'; });
    document.addEventListener('keydown',e=>{if(e.key==='Escape' && menu.getAttribute('aria-expanded')==='true'){closeMenu();menu.focus();}});
    document.addEventListener('click',e=>{if(!header.contains(e.target))closeMenu();});
    nav.addEventListener('click',e=>{if(e.target.closest('a'))closeMenu();});
    matchMedia('(min-width:701px)').addEventListener('change',closeMenu);
    const current=location.pathname.split('/').pop() || 'index.html';
    nav.querySelectorAll('a').forEach(a=>{a.removeAttribute('aria-current');if(new URL(a.href).pathname.split('/').pop()===current)a.setAttribute('aria-current','page');});
  }
  let scrollFrame;
  function updateScroll(){ scrollFrame=0; const height=document.documentElement.scrollHeight-innerHeight; progress.style.transform=`scaleX(${height>0?Math.min(1,scrollY/height):0})`; header?.classList.toggle('scrolled',scrollY>25); const show=scrollY>450;topButton.classList.toggle('visible',show);topButton.tabIndex=show?0:-1; }
  addEventListener('scroll',()=>{if(!scrollFrame)scrollFrame=requestAnimationFrame(updateScroll);},{passive:true});addEventListener('resize',updateScroll);addEventListener('load',updateScroll);updateScroll();
  // Only prepared observer targets are hidden; a fallback reveals all content.
  if('IntersectionObserver' in window && !reduce.matches){
    const items=[...document.querySelectorAll('main .card,main .panel,main .event,main .sectionhead')];
    const reveal=el=>{el.classList.add('is-visible');setTimeout(()=>{el.classList.remove('reveal-prep','reveal-ready');if(el.matches('.card')&&fine.matches&&!reduce.matches)el.classList.add('tilt');},850);};
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){reveal(entry.target);observer.unobserve(entry.target);}}),{threshold:.08});
    items.forEach((el,i)=>{el.style.setProperty('--delay',`${(i%3)*65}ms`);observer.observe(el);if(el.getBoundingClientRect().top>innerHeight){el.classList.add('reveal-prep');requestAnimationFrame(()=>el.classList.add('reveal-ready'));}});
    setTimeout(()=>{items.forEach(reveal);observer.disconnect();},6000);
    reduce.addEventListener('change',()=>{if(reduce.matches){items.forEach(reveal);observer.disconnect();}});
  }
  // Tilt is subtle and never replaces keyboard or touch interaction.
  document.querySelectorAll('main .card').forEach(card=>{
    if(!card.classList.contains('reveal-prep'))card.classList.add('tilt');
    card.addEventListener('pointermove',e=>{if(!fine.matches||reduce.matches||card.classList.contains('reveal-prep'))return;const r=card.getBoundingClientRect();card.style.setProperty('--rx',`${-(e.clientY-r.top-r.height/2)/r.height*3}deg`);card.style.setProperty('--ry',`${(e.clientX-r.left-r.width/2)/r.width*3}deg`);});
    card.addEventListener('pointerleave',()=>{card.style.removeProperty('--rx');card.style.removeProperty('--ry');});
  });
  const glow=make('div','cursor-glow');glow.setAttribute('aria-hidden','true');document.body.append(glow);
  let glowFrame=0,px=0,py=0;
  addEventListener('pointermove',e=>{if(!fine.matches||reduce.matches)return;px=e.clientX;py=e.clientY;if(!glowFrame)glowFrame=requestAnimationFrame(()=>{glow.style.transform=`translate3d(${px}px,${py}px,0)`;glow.classList.add('active');glowFrame=0;});},{passive:true});
  document.documentElement.addEventListener('pointerleave',()=>glow.classList.remove('active'));
  // Homepage enhancements do not alter editorial or medical claims.
  if((location.pathname.split('/').pop()||'index.html')==='index.html'){
    const h1=document.querySelector('.hero h1');if(h1){h1.replaceChildren(document.createTextNode('Bilgiyi paylaş,'),document.createElement('br'));const span=make('span','gradient-title');span.textContent='umudu bilimle büyüt.';h1.append(span);}
    const firstButton=document.querySelector('.hero .btn');if(firstButton){const actions=make('div','hero-actions');firstButton.before(actions);actions.append(firstButton);firstButton.textContent='İlaç kütüphanesini keşfet ↗';const news=make('a','btn secondary');news.href='haberler.html';news.textContent='Son haberler →';actions.append(news);}
    const hero=document.querySelector('.hero>div');if(hero){const line=make('p','type-line');line.setAttribute('aria-label','Kaynaklı bilgi, araştırma ve dayanışma.');const prefix=make('span','');prefix.setAttribute('aria-hidden','true');prefix.textContent='Birlikte: ';const word=make('span','type-word');word.setAttribute('aria-hidden','true');prefix.append(word);line.append(prefix);hero.append(line);const words=['bilgiye ulaşalım.','araştırmayı takip edelim.','dayanışmayı büyütelim.'];let wi=0,n=words[0].length,deleting=true,timer;word.textContent=words[0];const tick=()=>{if(reduce.matches||document.hidden)return;const text=words[wi];n+=deleting?-1:1;word.textContent=text.slice(0,n);let delay=deleting?38:72;if(n===0){deleting=false;wi=(wi+1)%words.length;delay=250;}else if(n===text.length&&!deleting){deleting=true;delay=2400;}timer=setTimeout(tick,delay);};const sync=()=>{clearTimeout(timer);if(reduce.matches){word.textContent=words[0];wi=0;n=words[0].length;deleting=true;}else if(!document.hidden)timer=setTimeout(tick,2400);};reduce.addEventListener('change',sync);document.addEventListener('visibilitychange',sync);sync();}
  }
  // Internal page exits respect modifier keys, downloads, anchors and BFCache.
  document.addEventListener('click',e=>{const a=e.target.closest('a');if(!a||e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.target||a.hasAttribute('download')||reduce.matches)return;const u=new URL(a.href,location.href);if(u.origin!==location.origin||!u.pathname.endsWith('.html')||u.pathname===location.pathname)return;e.preventDefault();document.body.classList.add('page-leaving');setTimeout(()=>location.assign(u.href),300);});
  addEventListener('pageshow',()=>document.body.classList.remove('page-leaving'));
  // Existing drug-library filtering remains authoritative.
  const filters=document.querySelectorAll('main select,main input[type=search]');
  filters.forEach(el=>el.addEventListener('change',()=>{document.querySelectorAll('main .card').forEach(card=>{card.classList.remove('filter-enter');requestAnimationFrame(()=>card.classList.add('filter-enter'));});}));
  document.querySelectorAll('table').forEach(table=>{const scroller=make('div','table-scroll');scroller.tabIndex=0;scroller.setAttribute('role','region');scroller.setAttribute('aria-label','Yatay kaydırılabilir bilgi tablosu');table.before(scroller);scroller.append(table);});
})();
