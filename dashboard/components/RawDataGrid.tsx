"use client";

import React, { useState } from 'react';
import { Table, Search, Eye, X, Filter } from 'lucide-react';

interface ListingItem {
  listing_id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  category: string;
  sub_category: string;
  location_city: string;
  location_region: string;
  posted_date: string;
  delisted_date: string | null;
  seller_type: string;
  source_platform: string;
  scraped_at: string;
}

interface RawDataGridProps {
  items: ListingItem[];
  total: number;
  page: number;
  onPageChange: (newPage: number) => void;
  search: string;
  onSearchChange: (q: string) => void;
  categoryFilter: string;
  onCategoryFilterChange: (cat: string) => void;
}

export const RawDataGrid: React.FC<RawDataGridProps> = ({
  items,
  total,
  page,
  onPageChange,
  search,
  onSearchChange,
  categoryFilter,
  onCategoryFilterChange,
}) => {
  const [selectedItem, setSelectedItem] = useState<ListingItem | null>(null);

  const getPlatformBadge = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'craigslist':
        return 'bg-purple-950/60 border-purple-500/50 text-purple-300';
      case 'facebook marketplace':
        return 'bg-blue-950/60 border-blue-500/50 text-blue-300';
      case 'offerup':
        return 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300';
      case 'ebay refurbished':
        return 'bg-amber-950/60 border-amber-500/50 text-amber-300';
      default:
        return 'bg-surface-high border-outline-variant text-outline';
    }
  };

  return (
    <div id="stream" className="bg-surface-container border border-outline-variant rounded-none p-5 shadow-sm">
      {/* Table Top Controls */}
      <div className="flex flex-wrap justify-between items-center mb-4 gap-4 border-b border-outline-variant pb-3">
        <div className="flex items-center gap-2">
          <Table className="w-4 h-4 text-primary" />
          <h2 className="text-xs font-mono font-bold text-primary tracking-widest uppercase">
            02 // RAW INGESTION PREVIEW STREAM ({total.toLocaleString()} RECORD BUFFER)
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-outline absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search title, city, ID..."
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              className="bg-surface-lowest border border-outline-variant pl-8 pr-3 py-1.5 text-xs font-mono text-white placeholder-outline focus:outline-none focus:border-primary w-48 sm:w-64"
            />
          </div>

          {/* Category Filter dropdown */}
          <div className="flex items-center gap-1.5 bg-surface-lowest border border-outline-variant px-2 py-1">
            <Filter className="w-3 h-3 text-outline" />
            <select
              value={categoryFilter}
              onChange={(e) => onCategoryFilterChange(e.target.value)}
              className="bg-transparent text-xs font-mono text-white focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-surface-container">All Categories</option>
              <option value="phones" className="bg-surface-container">Phones & Mobile</option>
              <option value="furniture" className="bg-surface-container">Furniture & Decor</option>
            </select>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="overflow-x-auto custom-scrollbar border border-outline-variant">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-surface-lowest border-b border-outline-variant text-outline uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-2.5 px-3">Listing ID / Time</th>
              <th className="py-2.5 px-3">Platform</th>
              <th className="py-2.5 px-3">Title</th>
              <th className="py-2.5 px-3">Category & Subcat</th>
              <th className="py-2.5 px-3 text-right">Scraped Price</th>
              <th className="py-2.5 px-3">Location</th>
              <th className="py-2.5 px-3">Seller Type</th>
              <th className="py-2.5 px-3 text-center">Payload</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/40">
            {items.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-outline italic font-sans">
                  No scraped raw listings currently buffered. Click "START SCRAPE PIPELINE" above to stream listings.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.listing_id} className="hover:bg-surface-high/60 transition-colors">
                  <td className="py-2 px-3 text-[11px]">
                    <div className="text-primary font-semibold">{item.listing_id}</div>
                    <div className="text-[10px] text-outline">
                      {item.scraped_at ? item.scraped_at.split('T')[1]?.replace('Z', '') : ''}
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 border text-[10px] uppercase ${getPlatformBadge(item.source_platform)}`}>
                      {item.source_platform}
                    </span>
                  </td>
                  <td className="py-2 px-3 max-w-xs truncate text-white font-sans text-xs" title={item.title}>
                    {item.title}
                  </td>
                  <td className="py-2 px-3">
                    <div className="text-white text-[11px]">{item.category}</div>
                    <div className="text-[10px] text-tertiary">{item.sub_category}</div>
                  </td>
                  <td className="py-2 px-3 text-right font-bold text-secondary text-sm">
                    ${item.price.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-outline">
                    {item.location_city}, {item.location_region}
                  </td>
                  <td className="py-2 px-3 text-[11px] text-outline">{item.seller_type}</td>
                  <td className="py-2 px-3 text-center">
                    <button
                      onClick={() => setSelectedItem(item)}
                      className="p-1 text-primary hover:bg-primary/20 rounded transition-colors"
                      title="Inspect Raw JSON"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex justify-between items-center mt-3 font-mono text-xs text-outline">
        <div>
          Showing {items.length} records (Buffer Total: {total.toLocaleString()})
        </div>
        <div className="flex gap-2">
          <button
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="px-3 py-1 border border-outline-variant bg-surface-lowest hover:text-white disabled:opacity-40"
          >
            PREV
          </button>
          <span className="px-3 py-1 text-primary font-bold">PAGE {page}</span>
          <button
            disabled={items.length < 10 || page * 10 >= total}
            onClick={() => onPageChange(page + 1)}
            className="px-3 py-1 border border-outline-variant bg-surface-lowest hover:text-white disabled:opacity-40"
          >
            NEXT
          </button>
        </div>
      </div>

      {/* Raw JSON Modal Viewer */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-surface-lowest border border-primary w-full max-w-2xl max-h-[80vh] flex flex-col font-mono text-xs">
            <div className="bg-surface-container px-4 py-2 border-b border-outline-variant flex justify-between items-center">
              <span className="text-primary font-bold">RAW JSON PAYLOAD // {selectedItem.listing_id}</span>
              <button onClick={() => setSelectedItem(null)} className="text-outline hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <pre className="p-4 overflow-y-auto custom-scrollbar text-secondary bg-black/90 text-xs leading-relaxed">
              {JSON.stringify(selectedItem, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
