export type AuthUser = {
  id: string;
  name: string;
  email: string;
  is_demo?: boolean;
  email_verified_at?: string | null;
  account_status?: string;
  created_at?: string | null;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
  expires_in?: number;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
};

export type AuthSession = {
  id: string;
  created_at: string;
  last_used_at?: string | null;
  expires_at: string;
  current_session: boolean;
  device: string;
  revoked: boolean;
};

export type RegisterPayload = {
  name: string;
  email: string;
  password: string;
};
