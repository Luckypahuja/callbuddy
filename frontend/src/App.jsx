import { useEffect, useState } from "react";
import "./App.css";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import CallingBuddy from "./pages/CallingBuddy";
import AIDoctor from "./pages/AIDoctor";
import SignSeeker from "./pages/SignSeeker";
export default function App() { const [path, setPath] = useState(window.location.pathname); const navigate = (nextPath) => { window.history.pushState({}, "", nextPath); setPath(nextPath); }; useEffect(() => { const h = () => setPath(window.location.pathname); window.addEventListener("popstate", h); return () => window.removeEventListener("popstate", h); }, []); const pages = { "/": <Home navigate={navigate} />, "/calling-buddy": <CallingBuddy navigate={navigate} />, "/ai-doctor": <AIDoctor navigate={navigate} />, "/sign-seeker": <SignSeeker navigate={navigate} /> }; return <div className="app-shell"><Navbar currentPath={path} navigate={navigate} />{pages[path] ?? <Home navigate={navigate} />}</div>; }
