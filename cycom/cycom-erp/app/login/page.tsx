'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User, Eye, EyeOff, Shield } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white flex flex-col justify-center items-center relative overflow-hidden p-6">
      {/* Background gradients */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-[#E67E22]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/3 w-[500px] h-[500px] bg-[#00F0FF]/5 rounded-full blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md bg-[#0B0F19] border border-white/5 p-8 rounded-2xl shadow-2xl relative z-10 space-y-6"
      >
        {/* Brand logo */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#E67E22] to-[#D35400] flex items-center justify-center shadow-lg shadow-orange-500/20 mx-auto">
            <span className="text-white font-black text-xl">C</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-wide">CYCOM ERP</h1>
          <p className="text-[10px] text-[#E67E22] uppercase tracking-widest font-bold">Cycom Portal</p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input 
                type="email" 
                required
                placeholder="name@cycom.jo" 
                className="input-field !pl-10 !py-3"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1.5 font-bold uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input 
                type={showPassword ? 'text' : 'password'} 
                required
                placeholder="••••••••" 
                className="input-field !pl-10 !pr-10 !py-3"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white flex items-center justify-center"
              >
                {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input type="checkbox" className="rounded bg-white/5 border-white/10" />
              <span>Remember me</span>
            </label>
            <a href="#" className="hover:underline text-cyan-400">Forgot password?</a>
          </div>

          {error && (
            <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 flex items-center justify-center gap-2 text-sm"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              'Sign In to Workspace'
            )}
          </button>
        </form>

        <div className="border-t border-white/5 pt-4 text-center text-[10px] text-slate-500 flex items-center justify-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-cyan-400" />
          <span>Secured with Single Device Hardware binding (cycom_mobile_single_device)</span>
        </div>
      </motion.div>
    </div>
  );
}
