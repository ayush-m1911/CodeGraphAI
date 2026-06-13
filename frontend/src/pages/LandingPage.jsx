import React from 'react';
import { motion } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { FaPlay, FaNetworkWired, FaGitAlt, FaSearch, FaCode } from 'react-icons/fa';
import { GiBrain } from 'react-icons/gi';

export const LandingPage = ({ onNavigate }) => {
  const { setIsArchModalOpen } = useApp();

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: 'spring', stiffness: 100, damping: 15 }
    }
  };

  const featureCards = [
    {
      icon: <FaGitAlt size={22} className="text-primary" />,
      title: "GitHub Auto-Ingestion",
      desc: "Provide any public Python GitHub repository URL and CodeGraphAI clones it dynamically."
    },
    {
      icon: <FaCode size={22} className="text-primary" />,
      title: "AST Parsing & Chunking",
      desc: "Tree-sitter analyzes classes, methods, and functions to split code logically rather than linearly."
    },
    {
      icon: <FaNetworkWired size={22} className="text-primary" />,
      title: "Knowledge Graph Generation",
      desc: "Maps inheritance trees, calls-flows, and contains connections between components."
    },
    {
      icon: <GiBrain size={22} className="text-primary" />,
      title: "Hybrid GraphRAG Reasoning",
      desc: "Resolves vector similarity, exact symbol match, and graph neighborhood lookups simultaneously."
    }
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="min-h-[90vh] flex flex-col justify-center items-center py-12 px-6 relative"
    >
      {/* Background Gold Ambient Spots */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] rounded-full bg-primary/5 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-[200px] h-[200px] rounded-full bg-primary/3 blur-[80px] pointer-events-none" />

      {/* Hero Content */}
      <div className="text-center max-w-4xl z-10 flex flex-col items-center">
        {/* Animated Badge */}
        <motion.div 
          variants={itemVariants}
          className="inline-flex items-center gap-2 px-3 py-1 bg-surface border border-primary/20 rounded-full text-xs font-semibold tracking-wider text-primary mb-6 shadow-[0_0_15px_rgba(212,175,55,0.05)]"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          GraphRAG REPOSITORY INTELLIGENCE
        </motion.div>

        {/* Title */}
        <motion.h1 
          variants={itemVariants}
          className="text-5xl md:text-7xl font-extrabold tracking-tight mb-4 select-text"
        >
          <span className="gold-text-gradient">CodeGraphAI</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.h2 
          variants={itemVariants}
          className="text-lg md:text-2xl font-medium text-text-secondary max-w-2xl leading-normal mb-6 select-text"
        >
          GraphRAG-Powered Repository Intelligence Assistant
        </motion.h2>

        {/* Description */}
        <motion.p 
          variants={itemVariants}
          className="text-sm md:text-base text-text-secondary/80 max-w-3xl leading-relaxed mb-10 select-text"
        >
          Understand any Python codebase through AST-aware retrieval, knowledge graph reasoning, and source-grounded AI answers. Connect your repository to build a developer assistant with architectural context.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div 
          variants={itemVariants}
          className="flex flex-col sm:flex-row gap-4 mb-20 w-full sm:w-auto"
        >
          <button
            onClick={() => onNavigate('setup')}
            className="flex items-center justify-center gap-2.5 px-8 py-3.5 bg-primary text-black font-bold rounded-lg hover:bg-primary-hover transition-all duration-300 shadow-[0_0_30px_rgba(212,175,55,0.15)] hover:shadow-[0_0_40px_rgba(212,175,55,0.3)] hover:scale-[1.02] active:scale-[0.98]"
          >
            <FaPlay size={13} />
            Analyze Repository
          </button>
          
          <button
            onClick={() => setIsArchModalOpen(true)}
            className="flex items-center justify-center gap-2.5 px-8 py-3.5 bg-surface border border-primary/20 text-text font-bold rounded-lg hover:bg-white/5 hover:border-primary/50 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] gold-border-pulse"
          >
            <FaNetworkWired size={14} className="text-primary" />
            View Architecture
          </button>
        </motion.div>
      </div>

      {/* Mini Feature Cards */}
      <motion.div 
        variants={itemVariants}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl w-full z-10"
      >
        {featureCards.map((card, idx) => (
          <motion.div
            key={idx}
            whileHover={{ y: -6 }}
            transition={{ type: 'spring', stiffness: 200, damping: 12 }}
            className="bg-surface border border-white/5 p-6 rounded-xl relative overflow-hidden group hover:border-primary/20 shadow-lg"
          >
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="w-10 h-10 rounded-lg bg-background border border-white/10 flex items-center justify-center mb-4 text-primary group-hover:border-primary/30 transition-all">
              {card.icon}
            </div>
            <h3 className="text-sm font-bold text-text mb-2 select-text">{card.title}</h3>
            <p className="text-xs text-text-secondary leading-relaxed select-text">{card.desc}</p>
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
};
export default LandingPage;
