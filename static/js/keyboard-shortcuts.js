// Keyboard Shortcuts System
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Key kombinasyonları
            if (e.ctrlKey || e.metaKey) {
                const key = e.key.toLowerCase();
                const shortcut = this.shortcuts.get(`ctrl+${key}`);
                if (shortcut) {
                    e.preventDefault();
                    shortcut.handler();
                }
            }

            // Alt + Key kombinasyonları
            if (e.altKey) {
                const key = e.key.toLowerCase();
                const shortcut = this.shortcuts.get(`alt+${key}`);
                if (shortcut) {
                    e.preventDefault();
                    shortcut.handler();
                }
            }

            // Sadece Key (Escape, F tuşları vb.)
            if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
                const shortcut = this.shortcuts.get(e.key);
                if (shortcut && !this.isInputFocused()) {
                    e.preventDefault();
                    shortcut.handler();
                }
            }
        });
    }

    isInputFocused() {
        const activeElement = document.activeElement;
        return activeElement && (
            activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.isContentEditable
        );
    }

    register(key, handler, description = '') {
        this.shortcuts.set(key.toLowerCase(), { handler, description });
    }

    unregister(key) {
        this.shortcuts.delete(key.toLowerCase());
    }
}

// Global instance
const keyboard = new KeyboardShortcuts();

// Varsayılan kısayollar
document.addEventListener('DOMContentLoaded', function() {
    // Ctrl+S: Kaydet (form varsa)
    keyboard.register('ctrl+s', () => {
        const form = document.querySelector('form');
        if (form && !form.querySelector('[type="search"]')) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.click();
        }
    }, 'Formu kaydet');

    // Ctrl+K: Arama
    keyboard.register('ctrl+k', () => {
        const searchInput = document.querySelector('input[type="search"], input[name="search"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }, 'Arama yap');

    // Escape: Modal/dialog kapat
    keyboard.register('Escape', () => {
        const modal = document.querySelector('.modal.show');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        }
    }, 'Modal kapat');

    // Alt+D: Dashboard
    keyboard.register('alt+d', () => {
        const dashboardLink = document.querySelector('a[href*="dashboard"]');
        if (dashboardLink) dashboardLink.click();
    }, 'Dashboard\'a git');

    // Alt+S: Stok
    keyboard.register('alt+s', () => {
        const stokLink = document.querySelector('a[href*="stok"]');
        if (stokLink) stokLink.click();
    }, 'Stok yönetimine git');

    // Alt+F: Fatura
    keyboard.register('alt+f', () => {
        const faturaLink = document.querySelector('a[href*="fatura"]');
        if (faturaLink) faturaLink.click();
    }, 'Fatura yönetimine git');

    // Alt+C: Cari
    keyboard.register('alt+c', () => {
        const cariLink = document.querySelector('a[href*="cari"]');
        if (cariLink) cariLink.click();
    }, 'Cari hesaplara git');
});

