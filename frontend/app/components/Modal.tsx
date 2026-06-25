import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  closeButton?: boolean;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeButton = true,
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClass = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  }[size];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className={`relative bg-white rounded-xl shadow-xl z-10 animate-slide-up w-full ${sizeClass}`}>
        {/* Header */}
        {(title || closeButton) && (
          <div className="flex items-start justify-between p-6 border-b border-neutral-200">
            {title && (
              <div>
                <h2 className="text-lg font-bold text-neutral-900">{title}</h2>
                {description && <p className="text-sm text-neutral-600 mt-1">{description}</p>}
              </div>
            )}
            {closeButton && (
              <button
                onClick={onClose}
                className="ml-4 p-1 hover:bg-neutral-100 rounded transition-colors"
              >
                <X className="h-5 w-5 text-neutral-400" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-6 max-h-96 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
};
