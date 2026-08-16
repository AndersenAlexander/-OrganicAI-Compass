import { AlertCircle, ArrowLeft, ArrowRight, BookOpen, CheckCircle2, Info, Lightbulb, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { OrganicPageBackdrop } from "../components/public/OrganicPageBackdrop";
import { PublicPageShell } from "../components/public/PublicPageShell";
import { getBlogArticle, getRelatedArticles, type BlogCallout } from "../data/blogArticles";
import "../styles/blog.css";

const calloutIcons:Record<BlogCallout["label"],typeof Info>={"RESEARCH CONTEXT":BookOpen,"DESIGN DECISION":Lightbulb,"IMPLEMENTATION NOTE":Info,"RESPONSIBLE AI BOUNDARY":ShieldCheck,"CURRENT LIMITATION":AlertCircle};
const sectionId=(heading:string,index:number)=>`${heading.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/(^-|-$)/g,"")}-${index+1}`;

export function BlogArticlePage(){
  const {slug}=useParams();const article=getBlogArticle(slug);
  document.title=article?`${article.title} - OrganicAI Journal`:"Journal entry not found - OrganicAI";
  if(!article)return <PublicPageShell><div className="organicai-article-page"><OrganicPageBackdrop/><section className="article-not-found"><span>ORGANICAI JOURNAL</span><h1>Journal entry not found</h1><p>The requested entry does not exist in the current research journal.</p><div><Link className="blog-button" to="/blog">Return to the Journal</Link><Link className="blog-button secondary" to="/research">Explore the Research</Link></div></section></div></PublicPageShell>;
  const related=getRelatedArticles(article);const headings=article.sections.map((section,index)=>section.heading?{heading:section.heading,id:sectionId(section.heading,index)}:null).filter(Boolean) as {heading:string;id:string}[];
  const contents=<nav aria-label="In this article"><b>In this article</b>{headings.map(item=><a key={item.id} href={`#${item.id}`}>{item.heading}</a>)}</nav>;
  return <PublicPageShell><article className="organicai-article-page"><OrganicPageBackdrop/><div className="article-container">
    <nav aria-label="Breadcrumb" className="article-breadcrumb"><Link to="/blog">Journal</Link><span>/</span><span>{article.category}</span><span>/</span><span>Article</span></nav>
    <header className="article-hero"><p className="blog-card-meta"><span>{article.contentType}</span><span>{article.category}</span></p><h1>{article.title}</h1><p>{article.excerpt}</p><div className="article-meta"><span>{article.readingTime}</span>{article.relatedRoutes.map(route=><Link key={route.to} to={route.to}>{route.label}</Link>)}</div><Link className="article-back" to="/blog"><ArrowLeft size={16}/> Back to Journal</Link></header>
    <details className="article-mobile-contents"><summary>In this article</summary>{contents}</details>
    <div className="article-layout"><aside>{contents}</aside><div className="article-body">{article.sections.map((section,index)=>{const id=section.heading?sectionId(section.heading,index):undefined;return <section id={id} key={id??index}>{section.heading&&<h2>{section.heading}</h2>}{section.paragraphs?.map((paragraph,p)=><p key={p}>{paragraph}</p>)}{section.bullets&&<ul>{section.bullets.map(item=><li key={item}><CheckCircle2 size={18}/>{item}</li>)}</ul>}{section.quote&&<blockquote>{section.quote}</blockquote>}{section.callout&&(()=>{const Icon=calloutIcons[section.callout.label];return <aside className={`article-callout callout-${section.callout.label.toLowerCase().replace(/ /g,"-")}`}><Icon size={22}/><div><b>{section.callout.label}</b><p>{section.callout.text}</p></div></aside>})()}</section>})}</div></div>
    <section className="article-related"><header><p>CONTINUE EXPLORING</p><h2>Related journal entries</h2></header><div>{related.map(item=><Link key={item.slug} to={`/blog/${item.slug}`}><span>{item.contentType}</span><h3>{item.title}</h3><small>{item.readingTime}</small><ArrowRight size={17}/></Link>)}</div><Link className="article-back" to="/blog"><ArrowLeft size={16}/> Back to all journal entries</Link></section>
  </div></article></PublicPageShell>;
}
