import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IoCloseSharp } from 'react-icons/io5';
import { 
  FaGitAlt, 
  FaCode, 
  FaDatabase, 
  FaNetworkWired, 
  FaArrowRight, 
  FaCogs 
} from 'react-icons/fa';
import { GiBrain } from 'react-icons/gi';
import { BsBoxes } from 'react-icons/bs';

export const ArchitectureModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const steps = [
    {
      icon: <FaGitAlt className="text-2xl text-primary" />,
      title: "1. GitHub Repository Ingestion",
      desc: "Clone repository from git provider and fetch all source files (.py, .js, .ts, etc.)."
    },
    {
      icon: <FaCode className="text-2xl text-primary" />,
      title: "2. Tree-sitter AST Parser",
      desc: "Parse source code into Concrete Syntax Trees (CST/AST) using language-specific parsers."
    },
    {
      icon: <BsBoxes className="text-2xl text-primary" />,
      title: "3. Class/Method AST Chunking",
      desc: "Split files into logical code chunks based on structural boundaries rather than character limits."
    },
    {
      icon: <FaCogs className="text-2xl text-primary" />,
      title: "4. Embedding Generation",
      desc: "Generate dense vectors using local BAAI/bge-small-en-v1.5 embedding models."
    },
    {
      icon: <FaDatabase className="text-2xl text-primary" />,
      title: "5. Qdrant Vector DB",
      desc: "Store embeddings and chunk payload metadata for fast similarity lookup."
    },
    {
      icon: <FaNetworkWired className="text-2xl text-primary" />,
      title: "6. Knowledge Graph Construction",
      desc: "Map method call flow, contains relations, and class inheritances from AST analysis."
    },
    {
      icon: <FaNetworkWired className="text-2xl text-primary" />,
      title: "7. Hybrid retrieval & Expansion",
      desc: "Combine vector matches with exact symbol lookup and knowledge graph expansion."
    },
    {
      icon: <GiBrain className="text-2xl text-primary" />,
      title: "8. Groq Llama 3 LLM",
      desc: "Inject context-rich graph code excerpts into llama-3.3-70b-versatile for synthesis."
    }
  ];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.8 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/95 backdrop-blur-sm"
        />

        {/* Modal content */}
        <motion.div
          initial={{ scale: 0.95, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 20 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="relative w-full max-w-4xl bg-surface border border-primary/20 rounded-xl overflow-hidden shadow-2xl z-10"
        >
          {/* Header */}
          <div className="flex justify-between items-center px-6 py-4 border-b border-white/10 bg-black/45">
            <div>
              <h2 className="text-xl font-bold tracking-wider text-primary">CodeGraphAI System Architecture</h2>
              <p className="text-xs text-text-secondary mt-0.5">Under the hood of AST-aware hybrid GraphRAG retrieval</p>
            </div>
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-primary transition-colors p-2 hover:bg-white/5 rounded-full"
            >
              <IoCloseSharp size={22} />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 md:p-8 max-h-[70vh] overflow-y-auto">
            {/* Visual Graph View */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              {steps.slice(0, 4).map((s, idx) => (
                <div key={idx} className="relative bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col items-center text-center">
                  <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mb-3">
                    {s.icon}
                  </div>
                  <h4 className="text-xs font-semibold text-text mb-1">{s.title.substring(3)}</h4>
                  <p className="text-[10px] text-text-secondary leading-normal">{s.desc}</p>
                  {idx < 3 && (
                    <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-20">
                      <FaArrowRight className="text-primary/30 text-xs" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              {steps.slice(4).map((s, idx) => (
                <div key={idx} className="relative bg-black/40 border border-white/5 p-4 rounded-lg flex flex-col items-center text-center">
                  <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mb-3">
                    {s.icon}
                  </div>
                  <h4 className="text-xs font-semibold text-text mb-1">{s.title.substring(3)}</h4>
                  <p className="text-[10px] text-text-secondary leading-normal">{s.desc}</p>
                  {idx < 3 && (
                    <div className="hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 z-20">
                      <FaArrowRight className="text-primary/30 text-xs" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Ingestion to Synthesis Diagram */}
            <div className="bg-black/85 border border-primary/10 rounded-lg p-5">
              <h3 className="text-sm font-semibold text-primary mb-3 uppercase tracking-wider">Retrieval flow details</h3>
              <div className="flex flex-col gap-3 text-xs text-text-secondary">
                <div className="flex items-start gap-2">
                  <span className="text-primary font-bold">Vector Search:</span>
                  <span>Computes cosine similarity between user query embeddings and code chunk vector index. Finds the top semantic files.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-primary font-bold">Exact Symbol Lookup:</span>
                  <span>Extracts words matching python variable patterns and executes exact string lookups in database indexes to catch direct dependencies.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-primary font-bold">Graph Expansion (GraphRAG):</span>
                  <span>Retrieves neighbors in the repository call-graph (calls, containment, subclass) for each identified code symbol. This captures surrounding context that semantic search alone misses.</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-primary font-bold">Groq LLM Generation:</span>
                  <span>Merges semantic matches + graph definitions + exact symbol hits into the LLM context limit to generate source-backed answers.</span>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center px-6 py-4 bg-black/40 border-t border-white/10 text-xs text-text-secondary">
            <span>GraphRAG Repository Intelligence Engine v1.0.0</span>
            <button 
              onClick={onClose}
              className="px-4 py-1.5 bg-primary text-black font-semibold rounded hover:bg-primary-hover transition-colors shadow-lg"
            >
              Done
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
export default ArchitectureModal;
