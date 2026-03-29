import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { SearchPage } from './pages/SearchPage';
import { FavoritesPage } from './pages/FavoritesPage';
import { SyncStatus } from './components/SyncStatus';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900">
        <nav className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-screen-2xl mx-auto px-6 flex items-center h-14">
            <span className="text-lg font-bold text-gray-100 mr-8">
              Motoren NL
            </span>
            <div className="flex gap-1">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
                  }`
                }
              >
                Search
              </NavLink>
              <NavLink
                to="/favorites"
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
                  }`
                }
              >
                Favorites
              </NavLink>
            </div>
            <div className="ml-auto">
              <SyncStatus />
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
