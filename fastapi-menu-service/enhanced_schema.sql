-- Enhanced Menu OCR Database Schema
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Update users table to include address and subscription info
ALTER TABLE IF EXISTS public.users 
ADD COLUMN IF NOT EXISTS address_street TEXT,
ADD COLUMN IF NOT EXISTS address_city TEXT,
ADD COLUMN IF NOT EXISTS address_state TEXT,
ADD COLUMN IF NOT EXISTS address_zip TEXT,
ADD COLUMN IF NOT EXISTS address_country TEXT DEFAULT 'US',
ADD COLUMN IF NOT EXISTS subscription_plan TEXT CHECK (subscription_plan IN ('free', 'basic', 'premium')) DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_status TEXT CHECK (subscription_status IN ('active', 'canceled', 'past_due', 'trialing')) DEFAULT 'free',
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS referral_code TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS referred_by UUID REFERENCES public.users(id),
ADD COLUMN IF NOT EXISTS referral_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP WITH TIME ZONE;

-- Create user addresses table for multiple addresses
CREATE TABLE IF NOT EXISTS public.user_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('home', 'work', 'delivery')) DEFAULT 'home',
    street TEXT NOT NULL,
    apartment_number TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT 'US',
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create pricing plans table
CREATE TABLE IF NOT EXISTS public.pricing_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    price_monthly_cents INTEGER NOT NULL,
    price_yearly_cents INTEGER,
    stripe_price_id_monthly TEXT NOT NULL,
    stripe_price_id_yearly TEXT,
    features JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user subscriptions table
CREATE TABLE IF NOT EXISTS public.user_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    plan_id UUID REFERENCES public.pricing_plans(id) NOT NULL,
    stripe_subscription_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing', 'incomplete')),
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create referrals table
CREATE TABLE IF NOT EXISTS public.referrals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    referrer_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    referee_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    referral_code TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'rewarded')) DEFAULT 'pending',
    reward_type TEXT CHECK (reward_type IN ('discount', 'credit', 'subscription_months')) DEFAULT 'subscription_months',
    reward_amount INTEGER DEFAULT 1, -- months
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_addresses_user_id ON public.user_addresses(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON public.user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_stripe_id ON public.user_subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON public.referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referee_id ON public.referrals(referee_id);
CREATE INDEX IF NOT EXISTS idx_referrals_code ON public.referrals(referral_code);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON public.users(referral_code);

-- Enable Row Level Security
ALTER TABLE public.user_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pricing_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referrals ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_addresses
CREATE POLICY "Users can view own addresses" 
    ON public.user_addresses FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own addresses" 
    ON public.user_addresses FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own addresses" 
    ON public.user_addresses FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own addresses" 
    ON public.user_addresses FOR DELETE 
    USING (auth.uid() = user_id);

-- RLS Policies for pricing_plans (public read)
CREATE POLICY "Anyone can view pricing plans" 
    ON public.pricing_plans FOR SELECT 
    USING (true);

-- RLS Policies for user_subscriptions
CREATE POLICY "Users can view own subscriptions" 
    ON public.user_subscriptions FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Service can manage subscriptions" 
    ON public.user_subscriptions FOR ALL 
    USING (auth.role() = 'service_role');

-- RLS Policies for referrals
CREATE POLICY "Users can view own referrals" 
    ON public.referrals FOR SELECT 
    USING (auth.uid() = referrer_id OR auth.uid() = referee_id);

CREATE POLICY "Users can create referrals" 
    ON public.referrals FOR INSERT 
    WITH CHECK (auth.uid() = referrer_id);

-- Update users updated_at trigger
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers for updated_at
CREATE TRIGGER update_user_addresses_updated_at 
    BEFORE UPDATE ON public.user_addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pricing_plans_updated_at 
    BEFORE UPDATE ON public.pricing_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at 
    BEFORE UPDATE ON public.user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_addresses TO authenticated;
GRANT SELECT ON public.pricing_plans TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_subscriptions TO authenticated;
GRANT SELECT, INSERT ON public.referrals TO authenticated;

-- Insert default pricing plans
INSERT INTO public.pricing_plans (name, description, price_monthly_cents, price_yearly_cents, stripe_price_id_monthly, stripe_price_id_yearly, features) VALUES
('Basic', 'Perfect for occasional use', 699, 6990, 'price_basic_monthly', 'price_basic_yearly', '["100 OCR scans per month", "Basic dish analysis", "Email support"]'),
('Premium', 'Best for frequent users', 999, 9990, 'price_premium_monthly', 'price_premium_yearly', '["Unlimited OCR scans", "Advanced AI analysis", "Health condition recommendations", "Priority support", "Export to PDF/Excel"]')
ON CONFLICT (name) DO UPDATE SET
    price_monthly_cents = EXCLUDED.price_monthly_cents,
    price_yearly_cents = EXCLUDED.price_yearly_cents,
    stripe_price_id_monthly = EXCLUDED.stripe_price_id_monthly,
    stripe_price_id_yearly = EXCLUDED.stripe_price_id_yearly,
    features = EXCLUDED.features;

-- Function to generate referral code
CREATE OR REPLACE FUNCTION generate_referral_code()
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER := 0;
BEGIN
    FOR i IN 1..8 LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to create user with referral code
CREATE OR REPLACE FUNCTION create_user_with_referral_code()
RETURNS TRIGGER AS $$
DECLARE
    new_code TEXT;
    code_exists BOOLEAN := true;
BEGIN
    -- Generate unique referral code
    WHILE code_exists LOOP
        new_code := generate_referral_code();
        SELECT EXISTS(SELECT 1 FROM public.users WHERE referral_code = new_code) INTO code_exists;
    END LOOP;
    
    NEW.referral_code := new_code;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically set referral code
DROP TRIGGER IF EXISTS set_referral_code ON public.users;
CREATE TRIGGER set_referral_code 
    BEFORE INSERT ON public.users
    FOR EACH ROW 
    EXECUTE FUNCTION create_user_with_referral_code();

-- Function to handle user registration with referral
CREATE OR REPLACE FUNCTION handle_new_user() 
RETURNS TRIGGER AS $$
DECLARE
    referrer_user_id UUID;
    referral_record_id UUID;
BEGIN
    -- If user was referred, update referral status
    IF NEW.referred_by IS NOT NULL THEN
        -- Update referral status
        INSERT INTO public.referrals (referrer_id, referee_id, referral_code, status, reward_type, reward_amount)
        VALUES (NEW.referred_by, NEW.id, 
                (SELECT referral_code FROM public.users WHERE id = NEW.referred_by),
                'completed', 'subscription_months', 1)
        ON CONFLICT DO NOTHING;
        
        -- Update referrer's referral count
        UPDATE public.users 
        SET referral_count = referral_count + 1 
        WHERE id = NEW.referred_by;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for new user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();