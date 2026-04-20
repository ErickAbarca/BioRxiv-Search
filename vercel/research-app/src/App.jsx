import React, { useState, useEffect } from 'react';
import { Search, User, LogOut, Mail, Lock, Eye, EyeOff, Filter, X, ChevronDown, ChevronUp } from 'lucide-react';

const API_BASE = 'https://2025-01-ic-4302-eight.vercel.app/api';

const App = () => {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('login');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [originalResults, setOriginalResults] = useState([]);
  const [facets, setFacets] = useState({});
  const [searchLoading, setSearchLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedFacets, setExpandedFacets] = useState({
    category: true,
    date: true,
    type: false,
    entities: false,
    authors: false,
    institutions: false
  });
  
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Filter states
  const [selectedFilters, setSelectedFilters] = useState({
    categories: [],
    dates: [],
    types: [],
    entities: [],
    authors: [],
    institutions: []
  });

  useEffect(() => {
    const savedUser = JSON.parse(sessionStorage.getItem('user') || 'null');
    if (savedUser) {
      setUser(savedUser);
      setCurrentView('search');
    }
  }, []);

  // Apply filters whenever selectedFilters changes
  useEffect(() => {
    if (originalResults.length > 0) {
      const filtered = getFilteredResults();
      setSearchResults(filtered);
    }
  }, [selectedFilters, originalResults]);

  const handleAuth = async (isLogin) => {
    if (!email || !password) {
      setError('Please fill in both fields');
      return;
    }

    setLoading(true);
    setError('');

    const endpoint = isLogin ? '/users/login' : '/users/register';
    
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        const userData = { email: data.email, apiKey: data.apiKey };
        setUser(userData);
        sessionStorage.setItem('user', JSON.stringify(userData));
        setCurrentView('search');
        setEmail('');
        setPassword('');
      } else {
        setError(data.message || 'Error: Wrong email or password');
      }
    } catch (err) {
      setError('Network error, please try again later');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      return;
    }

    setSearchLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`, {
        method: 'GET',
        headers: {
          'x-api-key': user.apiKey,
        },
      });

      const data = await response.json();

      if (response.ok) {
        const results = data.results || [];
        setOriginalResults(results);
        setSearchResults(results);
        
        // Transform facets to match expected structure
        const transformedFacets = {
          category_facet: data.category_facet || [],
          date_facet: data.date_facet || [],
          type_facet: data.type_facet || [],
          entities_facet: data.entities_facet || [],
          author_name_facet: data.author_name_facet || [],
          author_inst_facet: data.author_inst_facet || []
        };
        
        setFacets(transformedFacets);
        setShowFilters(true);
        
        // Clear previous filters when new search is performed
        setSelectedFilters({
          categories: [],
          dates: [],
          types: [],
          entities: [],
          authors: [],
          institutions: []
        });
      } else {
        setError('Search failed: ' + (data.message || 'Unknown error'));
        setSearchResults([]);
        setOriginalResults([]);
        setFacets({});
      }
    } catch (err) {
      setError('Search failed: Network error, please try again later');
      setSearchResults([]);
      setOriginalResults([]);
      setFacets({});
    } finally {
      setSearchLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    sessionStorage.removeItem('user');
    setCurrentView('login');
    setSearchQuery('');
    setSearchResults([]);
    setOriginalResults([]);
    setFacets({});
    setSelectedFilters({
      categories: [],
      dates: [],
      types: [],
      entities: [],
      authors: [],
      institutions: []
    });
    setEmail('');
    setPassword('');
    setError('');
    setShowFilters(false);
  };

const formatDate = (dateInput) => {
  try {
    // If dateInput is already a Date object or ISO string, parse it
    let date;
    if (typeof dateInput === 'string') {
      // Check if it's an ISO date string
      if (dateInput.match(/^\d{4}-\d{2}-\d{2}T/)) {
        date = new Date(dateInput);
      } else {
        // Assume it's in dd/mm/yyyy format
        const [day, month, year] = dateInput.split('/');
        date = new Date(`${year}-${month}-${day}`);
      }
    } else if (dateInput instanceof Date) {
      date = dateInput;
    } else {
      return 'Invalid Date';
    }

    // Check if the date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (error) {
    console.error(`Error parsing date: ${dateInput}`, error);
    return 'Invalid Date';
  }
};

const formatDateBoundary = (boundary) => {
  try {
    const date = new Date(boundary);
    if (isNaN(date.getTime())) {
      return boundary;
    }
    return (date.getUTCFullYear()).toString();
  } catch {
    return boundary;
  }
};

  const toggleFilter = (filterType, value) => {
    setSelectedFilters(prev => {
      const currentFilters = prev[filterType] || [];
      const isSelected = currentFilters.includes(value);
      
      return {
        ...prev,
        [filterType]: isSelected 
          ? currentFilters.filter(f => f !== value)
          : [...currentFilters, value]
      };
    });
  };

  const clearAllFilters = () => {
    setSelectedFilters({
      categories: [],
      dates: [],
      types: [],
      entities: [],
      authors: [],
      institutions: []
    });
  };

  const getFilteredResults = () => {
  if (!originalResults.length) return [];

  return originalResults.filter(result => {
    // Category filter
    if (selectedFilters.categories.length > 0 && 
        !selectedFilters.categories.includes(result.category)) {
      return false;
    }

    // Date filter
    if (selectedFilters.dates.length > 0) {
      const hasOtherSelected = selectedFilters.dates.includes('Other');
      const yearFilters = selectedFilters.dates.filter(d => d !== 'Other');

      if (result.rel_date) {
        // Parse rel_date as a Date object
        const date = new Date(result.rel_date);
        if (isNaN(date.getTime())) {
          // If rel_date is invalid, only include if "Other" is selected
          return hasOtherSelected;
        }
        // Get the year from rel_date
        const resultYear = date.getUTCFullYear().toString();
        // Map selected filter years to their corresponding bucket boundaries
        // Selected year (e.g., 2024) corresponds to bucket starting at 2023-01-01
        const mappedYears = yearFilters.map(year => (parseInt(year) - 1).toString());
        // Check if the document's year matches any selected bucket
        if (yearFilters.length > 0 && !mappedYears.includes((parseInt(resultYear) - 1).toString())) {
          return hasOtherSelected; // Include if "Other" is selected, otherwise exclude
        }
      } else {
        // No rel_date, only include if "Other" is selected
        return hasOtherSelected;
      }
    }

    // Type filter
    if (selectedFilters.types.length > 0 && 
        !selectedFilters.types.includes(result.type)) {
      return false;
    }

    // Entities filter
    if (selectedFilters.entities.length > 0) {
      if (!result.entities || !Array.isArray(result.entities)) {
        return false;
      }
      const hasMatchingEntity = result.entities.some(entity => 
        selectedFilters.entities.includes(entity)
      );
      if (!hasMatchingEntity) return false;
    }

    // Authors filter
    if (selectedFilters.authors.length > 0) {
      if (!result.authors || !Array.isArray(result.authors)) {
        return false;
      }
      const hasMatchingAuthor = result.authors.some(author => 
        selectedFilters.authors.includes(author.author_name)
      );
      if (!hasMatchingAuthor) return false;
    }

    // Institutions filter
    if (selectedFilters.institutions.length > 0) {
      if (!result.authors || !Array.isArray(result.authors)) {
        return false;
      }
      const hasMatchingInstitution = result.authors.some(author => 
        author.author_inst && Array.isArray(author.author_inst) &&
        author.author_inst.some(inst => selectedFilters.institutions.includes(inst))
      );
      if (!hasMatchingInstitution) return false;
    }

    return true;
  });
};

  const toggleFacetExpansion = (facetName) => {
    setExpandedFacets(prev => ({
      ...prev,
      [facetName]: !prev[facetName]
    }));
  };

  // Function to highlight search terms in abstract
  const highlightAbstract = (abstract, highlights) => {
    if (!highlights || highlights.length === 0) {
      return <span>{abstract}</span>;
    }

    // Get all hit terms from highlights
    const hitTerms = new Set();
    highlights.forEach(highlight => {
      highlight.texts.forEach(text => {
        if (text.type === 'hit') {
          hitTerms.add(text.value.toLowerCase());
        }
      });
    });

    if (hitTerms.size === 0) {
      return <span>{abstract}</span>;
    }

    // Create a regex pattern for all hit terms
    const pattern = Array.from(hitTerms)
      .map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
      .join('|');
    
    const regex = new RegExp(`(${pattern})`, 'gi');
    const parts = abstract.split(regex);

    return (
      <span>
        {parts.map((part, index) => {
          const isHit = hitTerms.has(part.toLowerCase());
          return isHit ? (
            <span key={index} className="bg-yellow-200 text-yellow-900 px-1 py-0.5 rounded font-semibold">
              {part}
            </span>
          ) : (
            <span key={index}>{part}</span>
          );
        })}
      </span>
    );
  };

  const FacetSection = ({ title, facetKey, data, filterKey, formatValue = (v) => v }) => {
    if (!data || data.length === 0) return null;
    
    const isExpanded = expandedFacets[facetKey];
    const displayData = isExpanded ? data.slice(0, 15) : data.slice(0, 5);
    
    return (
      <div className="mb-6">
        <button
          onClick={() => toggleFacetExpansion(facetKey)}
          className="flex items-center justify-between w-full text-left font-semibold text-gray-900 mb-3 hover:text-indigo-600 transition-colors"
        >
          <span>{title}</span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        
        {isExpanded && (
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {displayData.map((item, index) => {
              const isSelected = selectedFilters[filterKey].includes(item._id);
              return (
                <label key={index} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-1 rounded transition-colors">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleFilter(filterKey, item._id)}
                    className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                  />
                  <span className={`text-sm flex-1 ${isSelected ? 'text-indigo-700 font-medium' : 'text-gray-700'}`}>
                    {formatValue(item._id)}
                  </span>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full min-w-[2rem] text-center">
                    {item.count}
                  </span>
                </label>
              );
            })}
            {data.length > displayData.length && (
              <button
                onClick={() => toggleFacetExpansion(facetKey)}
                className="text-xs text-indigo-600 hover:text-indigo-800 ml-6"
              >
                {isExpanded ? 'Show less' : `Show ${data.length - displayData.length} more`}
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

  if (currentView === 'search' && user) {
    const activeFiltersCount = Object.values(selectedFilters).flat().length;

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <Search className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold text-gray-900">Research Explorer</h1>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <User className="w-4 h-4" />
                  <span>{user.email}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Salir</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Search Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Search Scientific Articles
            </h2>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Enter keywords, topics, or authors..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none text-lg"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={searchLoading || !searchQuery.trim()}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2 font-medium"
              >
                {searchLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Search className="w-5 h-5" />
                )}
                <span>{searchLoading ? 'Searching...' : 'Search'}</span>
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Main Content Area */}
          {originalResults.length > 0 && (
            <div className="flex gap-6">
              {/* Filters Sidebar */}
              {showFilters && (
                <div className="w-80 flex-shrink-0">
                  <div className="bg-white rounded-xl shadow-lg p-6 sticky top-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <Filter className="w-5 h-5 mr-2" />
                        Filters
                        {activeFiltersCount > 0 && (
                          <span className="ml-2 bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full text-xs font-medium">
                            {activeFiltersCount}
                          </span>
                        )}
                      </h3>
                      {activeFiltersCount > 0 && (
                        <button
                          onClick={clearAllFilters}
                          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                        >
                          Clear all
                        </button>
                      )}
                    </div>

                    <div className="space-y-1">
                      <FacetSection
                        title="Category"
                        facetKey="category"
                        data={facets.category_facet}
                        filterKey="categories"
                      />
                      
                      <FacetSection
                        title="Publication Date"
                        facetKey="date"
                        data={facets.date_facet}
                        filterKey="dates"
                        formatValue={formatDateBoundary}
                      />
                      
                      <FacetSection
                        title="Document Type"
                        facetKey="type"
                        data={facets.type_facet}
                        filterKey="types"
                      />
                      
                      <FacetSection
                        title="Key Entities"
                        facetKey="entities"
                        data={facets.entities_facet}
                        filterKey="entities"
                      />
                      
                      <FacetSection
                        title="Authors"
                        facetKey="authors"
                        data={facets.author_name_facet}
                        filterKey="authors"
                      />
                      
                      <FacetSection
                        title="Institutions"
                        facetKey="institutions"
                        data={facets.author_inst_facet}
                        filterKey="institutions"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Results Area */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">
                    Search Results ({searchResults.length})
                    {searchResults.length !== originalResults.length && (
                      <span className="text-sm text-gray-500 ml-2">
                        (filtered from {originalResults.length})
                      </span>
                    )}
                  </h3>
                  
                  {!showFilters && originalResults.length > 0 && (
                    <button
                      onClick={() => setShowFilters(true)}
                      className="flex items-center space-x-1 text-sm text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-3 py-2 rounded-md"
                    >
                      <Filter className="w-4 h-4" />
                      <span>Show Filters</span>
                    </button>
                  )}
                </div>
                
                {/* Active Filters Display */}
                {activeFiltersCount > 0 && (
                  <div className="mb-6 p-4 bg-indigo-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-indigo-900">Active Filters:</span>
                      <button
                        onClick={clearAllFilters}
                        className="text-xs text-indigo-600 hover:text-indigo-800"
                      >
                        Clear all
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(selectedFilters).map(([filterType, values]) =>
                        values.map((value) => (
                          <span
                            key={`${filterType}-${value}`}
                            className="inline-flex items-center gap-1 bg-indigo-100 text-indigo-800 text-xs px-2 py-1 rounded-full"
                          >
                            {value}
                            <button
                              onClick={() => toggleFilter(filterType, value)}
                              className="hover:bg-indigo-200 rounded-full p-0.5"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                )}
                
                <div className="space-y-6">
                  {searchResults.map((result, index) => (
                    <div key={result._id || index} className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-100">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h4 className="text-lg font-bold text-gray-900 mb-2 leading-tight">
                            {result.title}
                          </h4>
                          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-3">
                            {result.category && (
                              <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full font-medium">
                                {result.category}
                              </span>
                            )}
                            {result.rel_date && (
                              <span>{formatDate(result.rel_date)}</span>
                            )}
                            {result.type && (
                              <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full font-medium">
                                {result.type}
                              </span>
                            )}
                            {result.score && (
                              <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
                                Score: {result.score.toFixed(2)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="text-gray-700 mb-4 leading-relaxed">
                        {highlightAbstract(result.abstract, result.highlights)}
                      </div>

                      {result.highlights && result.highlights.length > 0 && (
                        <div className="mb-4">
                          <h5 className="font-semibold text-gray-900 mb-2">Relevant Fragments</h5>
                          <div className="space-y-2">
                            {result.highlights.map((highlight, idx) => (
                              <div key={idx} className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                                <p className="text-sm">
                                  {highlight.texts.map((text, textIdx) => (
                                    <span key={textIdx} className={text.type === 'hit' ? 'bg-yellow-200 font-semibold px-1 rounded' : ''}>
                                      {text.value}
                                    </span>
                                  ))}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {result.authors && result.authors.length > 0 && (
                        <div className="mb-4">
                          <h5 className="font-semibold text-gray-900 mb-2">Authors:</h5>
                          <div className="flex flex-wrap gap-2">
                            {result.authors.slice(0, 5).map((author, idx) => (
                              <span key={idx} className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm">
                                {author.author_name}
                                {author.author_inst && author.author_inst.length > 0 && (
                                  <span className="text-xs text-gray-500 ml-1">
                                    ({author.author_inst[0]})
                                  </span>
                                )}
                              </span>
                            ))}
                            {result.authors.length > 5 && (
                              <span className="text-gray-500 text-sm">
                                +{result.authors.length - 5} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="flex justify-between items-center pt-4 border-t border-gray-100">
                        {result.link && (
                          <a
                            href={result.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-indigo-600 hover:text-indigo-800 font-medium hover:underline"
                          >
                            See complete article →
                          </a>
                        )}
                        {result.doi && (
                          <span className="text-xs text-gray-500 font-mono">
                            DOI: {result.doi}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {searchResults.length === 0 && originalResults.length > 0 && (
                  <div className="text-center py-12">
                    <Filter className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No results match your filters</h3>
                    <p className="text-gray-500 mb-4">Try adjusting your filter criteria</p>
                    <button
                      onClick={clearAllFilters}
                      className="text-indigo-600 hover:text-indigo-800 font-medium"
                    >
                      Clear all filters
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {originalResults.length === 0 && searchQuery && !searchLoading && !error && (
            <div className="text-center py-12">
              <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-500">Try different keywords or check your spelling</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Login/Register View
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-blue-50 to-cyan-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Research Explorer</h1>
            <p className="text-gray-600 mt-2">
              {currentView === 'login' ? 'Login with your account' : 'Create a new account'}
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-6">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  placeholder="tu@email.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              onClick={() => handleAuth(currentView === 'login')}
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center space-x-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <span>{currentView === 'login' ? 'Login' : 'Register'}</span>
              )}
            </button>

            <div className="text-center">
              <button
                onClick={() => {
                  setCurrentView(currentView === 'login' ? 'register' : 'login');
                  setError('');
                  setEmail('');
                  setPassword('');
                }}
                className="text-indigo-600 hover:text-indigo-800 font-medium"
              >
                {currentView === 'login' 
                  ? '¿Do not have an account? Register' 
                  : '¿Have an account? Login'
                }
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;