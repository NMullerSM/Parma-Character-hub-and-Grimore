/**
 * Safe Storage Abstraction
 * Protege contra 'ReferenceError: Can't find variable: localStorage'
 * y SecurityError en WebKitGTK / Safari / Private Browsing / WebViews.
 */

class MemoryStorage implements Storage {
  private memory = new Map<string, string>();

  get length(): number {
    return this.memory.size;
  }

  key(index: number): string | null {
    return Array.from(this.memory.keys())[index] ?? null;
  }

  getItem(key: string): string | null {
    return this.memory.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.memory.set(key, String(value));
  }

  removeItem(key: string): void {
    this.memory.delete(key);
  }

  clear(): void {
    this.memory.clear();
  }
}

const memoryFallback = new MemoryStorage();

function getNativeStorage(): Storage | null {
  try {
    if (typeof window !== "undefined" && "localStorage" in window && window.localStorage) {
      const testKey = "__parma_storage_probe__";
      window.localStorage.setItem(testKey, "1");
      window.localStorage.removeItem(testKey);
      return window.localStorage;
    }
  } catch {
    // Almacenamiento restringido, bloqueado por sandbox o no disponible en WebKitGTK
  }
  return null;
}

export const safeStorage = {
  getItem(key: string): string | null {
    try {
      const native = getNativeStorage();
      if (native) return native.getItem(key);
    } catch {
      // Ignorar fallo y usar memoria
    }
    return memoryFallback.getItem(key);
  },

  setItem(key: string, value: string): void {
    try {
      const native = getNativeStorage();
      if (native) {
        native.setItem(key, String(value));
        return;
      }
    } catch {
      // Ignorar fallo y usar memoria
    }
    memoryFallback.setItem(key, String(value));
  },

  removeItem(key: string): void {
    try {
      const native = getNativeStorage();
      if (native) {
        native.removeItem(key);
        return;
      }
    } catch {
      // Ignorar fallo y usar memoria
    }
    memoryFallback.removeItem(key);
  },

  clear(): void {
    try {
      const native = getNativeStorage();
      if (native) {
        native.clear();
        return;
      }
    } catch {
      // Ignorar fallo y usar memoria
    }
    memoryFallback.clear();
  },
};

// Polyfill defensivo para asegurar que window.localStorage y globalThis.localStorage nunca sean undefined
if (typeof window !== "undefined") {
  try {
    if (!window.localStorage) {
      (window as any).localStorage = safeStorage;
    }
  } catch {
    try {
      Object.defineProperty(window, "localStorage", {
        value: safeStorage,
        writable: true,
        configurable: true,
      });
    } catch {
      // Ignorar si el motor bloquea defineProperty
    }
  }
}
