import '@fontsource/anton'
import '@fontsource-variable/nunito'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './auth.tsx'
import { ChatBridgeProvider } from './chatBridge.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ChatBridgeProvider>
          <App />
        </ChatBridgeProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
