/* Menu, back-to-top, copy email. The page works without this script. */
(function(){
  var hdr=document.getElementById('site-header'),top=document.getElementById('to-top'),menu=document.getElementById('menu');
  function onScroll(){var y=window.scrollY||0;hdr.classList.toggle('scrolled',y>8);top.hidden=y<window.innerHeight;}
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  if(menu){menu.addEventListener('click',function(e){if(e.target.closest('a'))menu.removeAttribute('open');});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&menu.open){menu.removeAttribute('open');menu.querySelector('summary').focus();}});}
  var cb=document.getElementById('copy-email'),st=document.getElementById('copy-status'),mail='benedictisaac258@gmail.com';
  if(cb){cb.addEventListener('click',function(){
    function done(ok){cb.textContent=ok?'Copied':'Copy email';st.textContent=ok?'Email address copied.':'Copy did not work. The address is: '+mail;setTimeout(function(){cb.textContent='Copy email';},2000);}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(mail).then(function(){done(true)},function(){done(false)});}
    else{var t=document.createElement('textarea');t.value=mail;document.body.appendChild(t);t.select();var ok=false;try{ok=document.execCommand('copy')}catch(x){}document.body.removeChild(t);done(ok);}
  });}
})();
