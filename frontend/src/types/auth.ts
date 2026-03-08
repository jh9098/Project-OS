export type User = {
  id: string;
  username: string;
  role: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};
