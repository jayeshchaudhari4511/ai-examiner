export const setStoredUser = (user) => {
  if (user) {
    localStorage.setItem('current_user', JSON.stringify(user));
  }
};

export const getStoredUser = () => {
  const raw = localStorage.getItem('current_user');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
};

export const clearStoredUser = () => {
  localStorage.removeItem('current_user');
};
