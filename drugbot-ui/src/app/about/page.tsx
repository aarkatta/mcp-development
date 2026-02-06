import { Pill, Shield, Search, Sparkles, AlertTriangle, Database } from 'lucide-react';

const features = [
  {
    icon: Search,
    title: "Drug Information",
    description: "Search for detailed information about medications, including usage, dosage, and active ingredients from FDA-approved labels.",
    iconClass: "ai-icon-purple",
  },
  {
    icon: AlertTriangle,
    title: "Side Effects & Adverse Events",
    description: "Access FDA adverse event reports to understand potential side effects and safety concerns for any medication.",
    iconClass: "ai-icon-blue",
  },
  {
    icon: Shield,
    title: "Drug Recalls",
    description: "Stay informed about recent drug recalls, including classification levels (Class I, II, III) and affected products.",
    iconClass: "ai-icon-teal",
  },
  {
    icon: Database,
    title: "Drug Shortages",
    description: "Check current drug shortage information, availability status, and alternative options from FDA data.",
    iconClass: "ai-icon-purple",
  },
  {
    icon: Sparkles,
    title: "AI-Powered Analysis",
    description: "Powered by advanced AI that interprets FDA data and provides clear, actionable responses to your pharmaceutical queries.",
    iconClass: "ai-icon-blue",
  },
  {
    icon: Pill,
    title: "MCP Architecture",
    description: "Built on the Model Context Protocol (MCP) standard, connecting AI capabilities with real-time FDA data sources.",
    iconClass: "ai-icon-teal",
  },
];

export default function AboutPage() {
  return (
    <div className="container max-w-4xl mx-auto px-4 py-12">
      <div className="text-center mb-12">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl ai-gradient-bg mx-auto mb-6">
          <Pill className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold mb-4 ai-gradient-text">About DrugBot</h1>
        <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
          DrugBot is an AI-powered pharmaceutical assistant that provides real-time information about medications using FDA open data through the Model Context Protocol (MCP).
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <div
              key={index}
              className="flex gap-4 rounded-xl border bg-card p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Icon className={`h-5 w-5 ${feature.iconClass}`} />
              </div>
              <div>
                <h3 className="font-semibold mb-1">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded-xl border bg-card p-8 text-center">
        <h2 className="text-xl font-semibold mb-3 ai-gradient-text">How It Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-6">
          <div className="flex flex-col items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full ai-gradient-bg text-white font-bold">
              1
            </div>
            <h4 className="font-medium">Ask a Question</h4>
            <p className="text-xs text-muted-foreground">Type your medication question in the chat</p>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full ai-gradient-bg text-white font-bold">
              2
            </div>
            <h4 className="font-medium">AI Queries FDA</h4>
            <p className="text-xs text-muted-foreground">DrugBot uses MCP tools to fetch real-time FDA data</p>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-full ai-gradient-bg text-white font-bold">
              3
            </div>
            <h4 className="font-medium">Get Answers</h4>
            <p className="text-xs text-muted-foreground">Receive clear, sourced information with context</p>
          </div>
        </div>
      </div>

      <div className="mt-8 rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center">
        <p className="text-sm text-muted-foreground">
          <strong className="text-foreground">Disclaimer:</strong> DrugBot is for informational purposes only.
          Always consult a qualified healthcare professional before making any medical decisions.
          The information provided is sourced from FDA public data and may not be complete or up-to-date.
        </p>
      </div>
    </div>
  );
}
