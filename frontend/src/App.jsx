import React, { useEffect, useState } from 'react';

const PRODUCT_API = import.meta.env.VITE_PRODUCT_API || '/api/products';
const ORDER_API = import.meta.env.VITE_ORDER_API || '/api/orders';
const AI_API = import.meta.env.VITE_AI_API || '/api/ai';

export default function App() {
  const [products, setProducts] = useState([]);
  const [shown, setShown] = useState([]);
  const [query, setQuery] = useState('');
  const [cart, setCart] = useState({});
  const [chat, setChat] = useState([{role:'assistant', text:'Hi! Tell me what you are shopping for. For example: suggest a laptop under ₹60,000.'}]);
  const [message, setMessage] = useState('');
  const [customer, setCustomer] = useState('Demo Customer');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { fetch(PRODUCT_API).then(r=>r.json()).then(p=>{setProducts(p);setShown(p)}).catch(()=>setNotice('Could not connect to Product Service. Start Docker Compose and refresh.')); }, []);
  const add = id => setCart(c=>({...c,[id]:(c[id]||0)+1}));
  const total = products.reduce((s,p)=>s+(cart[p.id]||0)*Number(p.price),0);
  async function search(e) {
    e?.preventDefault();
    if (!query.trim()) { setShown(products); return; }
    try { const r=await fetch(`${AI_API}/search?q=${encodeURIComponent(query)}`); const d=await r.json(); setShown(d.results); }
    catch { setNotice('AI search service is unavailable.'); }
  }
  async function ask(e) {
    e.preventDefault(); if (!message.trim() || busy) return;
    const userText=message; setMessage(''); setChat(c=>[...c,{role:'user',text:userText}]); setBusy(true);
    try {
      const r=await fetch(`${AI_API}/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:'web-demo',message:userText})});
      const d=await r.json(); setChat(c=>[...c,{role:'assistant',text:d.reply||d.detail||'Sorry, something went wrong.'}]);
    } catch { setChat(c=>[...c,{role:'assistant',text:'AI service is unavailable. Please check the containers.'}]); }
    finally { setBusy(false); }
  }
  async function checkout() {
    const items=Object.entries(cart).filter(([,q])=>q>0).map(([id,quantity])=>({product_id:Number(id),quantity}));
    if (!items.length) {setNotice('Add at least one product first.');return;}
    try {
      const r=await fetch(ORDER_API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer_name:customer,items})});
      const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Order failed');
      setNotice(`Order #${d.order_id} placed successfully. Total: ₹${Number(d.total).toLocaleString('en-IN')}`);
      setCart({});
    } catch(err) {setNotice(err.message);}
  }
  return <div className="page">
    <header><div className="brand">✦ AI Commerce Hub</div><span>Smart shopping, made simple</span><div className="cart-pill">🛒 {Object.values(cart).reduce((a,b)=>a+b,0)} items</div></header>
    <main>
      <section className="hero"><div><p className="eyebrow">YOUR SMART SHOPPING ASSISTANT</p><h1>Find what you love.<br/><em>Shop smarter.</em></h1><p>Explore products with AI-powered search, recommendations and conversational assistance.</p></div><div className="hero-icon">✧</div></section>
      {notice && <div className="notice" onClick={()=>setNotice('')}>{notice}　×</div>}
      <form className="search" onSubmit={search}><span>⌕</span><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Try “affordable phone with good camera”"/><button>AI Search</button><button type="button" className="secondary" onClick={()=>{setQuery('');setShown(products)}}>Clear</button></form>
      <div className="layout">
        <section className="catalog"><div className="section-head"><div><p className="eyebrow">CURATED FOR YOU</p><h2>Explore products</h2></div><span>{shown.length} products</span></div>
          <div className="products">{shown.map((p,i)=><article className="product" key={p.id}><div className={`product-art art${i%4}`}><span>{p.category}</span><strong>{p.name.split(' ').map(w=>w[0]).join('').slice(0,3)}</strong></div><div className="product-info"><small>{p.category}</small><h3>{p.name}</h3><p>{p.description}</p><div className="product-bottom"><b>₹{Number(p.price).toLocaleString('en-IN')}</b><button onClick={()=>add(p.id)}>Add +</button></div></div></article>)}</div>
          {!shown.length && <p>No matching products. Try another search.</p>}
        </section>
        <aside>
          <section className="panel"><p className="eyebrow">YOUR BAG</p><h2>Shopping cart</h2>{products.filter(p=>cart[p.id]).map(p=><div className="cart-row" key={p.id}><span>{p.name} × {cart[p.id]}</span><b>₹{(Number(p.price)*cart[p.id]).toLocaleString('en-IN')}</b></div>)}<div className="total"><span>Total</span><strong>₹{total.toLocaleString('en-IN')}</strong></div><input className="customer" value={customer} onChange={e=>setCustomer(e.target.value)} placeholder="Customer name"/><button className="checkout" onClick={checkout}>Place demo order</button></section>
          <section className="panel chatbot"><p className="eyebrow">AI SHOPPING ASSISTANT</p><h2>Ask AI anything</h2><div className="messages">{chat.map((m,i)=><div className={`bubble ${m.role}`} key={i}>{m.text}</div>)}</div><form className="chat-form" onSubmit={ask}><input value={message} onChange={e=>setMessage(e.target.value)} placeholder="Ask for a recommendation..."/><button disabled={busy}>➤</button></form><small>Local catalog-based assistant · MongoDB conversation history</small></section>
        </aside>
      </div>
    </main>
    <footer>AI Commerce Hub · Demo microservices application</footer>
  </div>;
}
