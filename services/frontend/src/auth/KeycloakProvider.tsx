import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import Keycloak from 'keycloak-js'
import { setAuthToken } from '../api/client'

// Check if auth is enabled (defaults to true)
const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED !== 'false'

interface AuthContextType {
  keycloak: Keycloak | null
  initialized: boolean
  authenticated: boolean
  authEnabled: boolean
  token: string | undefined
  logout: () => void
  login: () => void
  userInfo: {
    name?: string
    email?: string
    roles?: string[]
  }
}

const AuthContext = createContext<AuthContextType>({
  keycloak: null,
  initialized: false,
  authenticated: false,
  authEnabled: AUTH_ENABLED,
  token: undefined,
  logout: () => {},
  login: () => {},
  userInfo: {},
})

export const useAuth = () => useContext(AuthContext)

const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'https://auth.wellspringfields.com',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'blaze',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'blaze-app',
}

interface KeycloakProviderProps {
  children: ReactNode
}

export function KeycloakProvider({ children }: KeycloakProviderProps) {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null)
  const [initialized, setInitialized] = useState(!AUTH_ENABLED)
  const [authenticated, setAuthenticated] = useState(!AUTH_ENABLED)

  useEffect(() => {
    // Skip Keycloak init if auth is disabled
    if (!AUTH_ENABLED) {
      console.log('Auth disabled - running in no-auth mode')
      return
    }

    const kc = new Keycloak(keycloakConfig)

    kc.init({
      onLoad: 'login-required',
      checkLoginIframe: false,
      pkceMethod: 'S256',
    })
      .then((auth) => {
        setKeycloak(kc)
        setAuthenticated(auth)
        setInitialized(true)

        // Set auth token for API calls
        if (auth && kc.token) {
          setAuthToken(kc.token)
        }

        // Set up token refresh
        if (auth) {
          setInterval(() => {
            kc.updateToken(70)
              .then((refreshed) => {
                if (refreshed) {
                  console.log('Token refreshed')
                  setAuthToken(kc.token)
                }
              })
              .catch(() => {
                console.error('Failed to refresh token')
                kc.logout()
              })
          }, 60000)
        }
      })
      .catch((error) => {
        console.error('Keycloak init error:', error)
        setInitialized(true)
      })
  }, [])

  const logout = () => {
    if (AUTH_ENABLED && keycloak) {
      keycloak.logout({ redirectUri: window.location.origin })
    }
  }

  const login = () => {
    if (AUTH_ENABLED && keycloak) {
      keycloak.login()
    }
  }

  const userInfo = AUTH_ENABLED
    ? {
        name: keycloak?.tokenParsed?.name as string | undefined,
        email: keycloak?.tokenParsed?.email as string | undefined,
        roles: keycloak?.tokenParsed?.realm_access?.roles as string[] | undefined,
      }
    : {
        name: 'Local User',
        email: 'local@blazedashboard',
        roles: ['admin'],
      }

  if (!initialized) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Authenticating...</p>
        </div>
      </div>
    )
  }

  if (AUTH_ENABLED && !authenticated) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">Authentication required</p>
          <button
            onClick={login}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <AuthContext.Provider
      value={{
        keycloak,
        initialized,
        authenticated,
        authEnabled: AUTH_ENABLED,
        token: keycloak?.token,
        logout,
        login,
        userInfo,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
