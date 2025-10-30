import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import TemplateFatura from "./pages/TemplateFatura"
import CustomTemplate from "./pages/CustomTemplate"
import BasicExtraction from "./pages/BasicExtraction"
import TextOnly from "./pages/TextOnly"
import TablesOnly from "./pages/TablesOnly"
import ApiDocumentation from "./pages/ApiDocumentation"

function App() {
  return (
    <BrowserRouter>
      <SidebarProvider>
        <AppSidebar />
        <main className="w-full">
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
            <SidebarTrigger className="-ml-1" />
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">ePDF Analyzer</h1>
            </div>
          </header>
          <div className="flex flex-1 flex-col gap-4 p-4 lg:p-8">
            <Routes>
              <Route path="/" element={<Navigate to="/template-efatura" replace />} />
              <Route path="/template-efatura" element={<TemplateFatura />} />
              <Route path="/template-custom" element={<CustomTemplate />} />
              <Route path="/basic-extraction" element={<BasicExtraction />} />
              <Route path="/basic-text" element={<TextOnly />} />
              <Route path="/basic-tables" element={<TablesOnly />} />
              <Route path="/basic-metadata" element={<div>Metadata (Coming Soon)</div>} />
              <Route path="/api-documentation" element={<ApiDocumentation />} />
              <Route path="/api-reference" element={<ApiDocumentation />} />
              <Route path="/api-examples" element={<ApiDocumentation />} />
              <Route path="/api-schemas" element={<ApiDocumentation />} />
              <Route path="/guide" element={<div>Usage Guide (Coming Soon)</div>} />
              <Route path="/faq" element={<div>FAQ (Coming Soon)</div>} />
            </Routes>
          </div>
        </main>
      </SidebarProvider>
    </BrowserRouter>
  )
}

export default App
