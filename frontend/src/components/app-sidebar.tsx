import * as React from "react"
import { ChevronRight, FileText, FileSearch, Table, Code, BookOpen } from "lucide-react"
import { Link, useLocation } from "react-router-dom"

import { SearchForm } from "@/components/search-form"
import { VersionSwitcher } from "@/components/version-switcher"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"

const data = {
  versions: ["v1.0.0", "v1.1.0-beta"],
  navMain: [
    {
      title: "Template Extraction",
      icon: FileSearch,
      url: "#",
      items: [
        {
          title: "E-Fatura Analyzer",
          url: "/template-efatura",
          description: "Turkish e-invoice analysis with LLM",
        },
        {
          title: "Custom Template",
          url: "/template-custom",
          description: "Create your own extraction template",
        },
      ],
    },
    {
      title: "Basic Extraction",
      icon: FileText,
      url: "#",
      items: [
        {
          title: "Text + Tables",
          url: "/basic-extraction",
          description: "Extract text and tables page-by-page",
        },
        {
          title: "Text Only",
          url: "/basic-text",
          description: "Extract raw text from PDF",
        },
        {
          title: "Tables Only",
          url: "/basic-tables",
          description: "Extract tables with header detection",
        },
        {
          title: "Metadata",
          url: "/basic-metadata",
          description: "Get PDF metadata and properties",
        },
      ],
    },
    {
      title: "API Documentation",
      icon: Code,
      url: "#",
      items: [
        {
          title: "API Reference",
          url: "/api-reference",
          description: "Complete API endpoint documentation",
        },
        {
          title: "Request Examples",
          url: "/api-examples",
          description: "Code samples in multiple languages",
        },
        {
          title: "Response Schemas",
          url: "/api-schemas",
          description: "JSON response format documentation",
        },
      ],
    },
    {
      title: "Resources",
      icon: BookOpen,
      url: "#",
      items: [
        {
          title: "Usage Guide",
          url: "/guide",
          description: "Step-by-step usage instructions",
        },
        {
          title: "FAQ",
          url: "/faq",
          description: "Frequently asked questions",
        },
      ],
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <VersionSwitcher
          versions={data.versions}
          defaultVersion={data.versions[0]}
        />
        <SearchForm />
      </SidebarHeader>
      <SidebarContent className="gap-0">
        {data.navMain.map((item) => (
          <Collapsible
            key={item.title}
            title={item.title}
            defaultOpen
            className="group/collapsible"
          >
            <SidebarGroup>
              <SidebarGroupLabel
                asChild
                className="group/label text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              >
                <CollapsibleTrigger>
                  <item.icon className="mr-2 h-4 w-4" />
                  {item.title}{" "}
                  <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
                </CollapsibleTrigger>
              </SidebarGroupLabel>
              <CollapsibleContent>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {item.items.map((subItem) => (
                      <SidebarMenuItem key={subItem.title}>
                        <SidebarMenuButton asChild isActive={location.pathname === subItem.url}>
                          <Link to={subItem.url}>
                            <span>{subItem.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </CollapsibleContent>
            </SidebarGroup>
          </Collapsible>
        ))}
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
