import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IoCheckmarkCircleSharp, IoCloseCircleSharp, IoInformationCircleSharp } from 'react-icons/io5';
import { IoMdClose } from 'react-icons/io';

export const Toast = ({ message, type = 'success', onClose, duration = 4000 }) => {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  if (!message) return null;

  const icons = {
    success: <IoCheckmarkCircleSharp className="text-emerald-500 text-lg flex-shrink-0" />,
    error: <IoCloseCircleSharp className="text-rose-500 text-lg flex-shrink-0" />,
    info: <IoInformationCircleSharp className="text-primary text-lg flex-shrink-0" />,
  };

  const borders = {
    success: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-100',
    error: 'border-rose-500/30 bg-rose-950/20 text-rose-100',
    info: 'border-primary/30 bg-black/80 text-white',
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 pointer-events-none">
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.9 }}
          className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-md shadow-2xl max-w-sm ${borders[type]}`}
        >
          {icons[type]}
          <p className="text-xs font-medium leading-relaxed flex-1 select-text">{message}</p>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded text-text-secondary hover:text-text transition-colors flex-shrink-0"
          >
            <IoMdClose size={14} />
          </button>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default Toast;
