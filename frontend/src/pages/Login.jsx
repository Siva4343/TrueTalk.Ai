import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, Mail, Lock, Eye, EyeOff } from 'lucide-react';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        
        // Simulate login process
        setTimeout(() => {
            setLoading(false);
            // Store user info in localStorage
            localStorage.setItem('teams_user_name', email.split('@')[0] || 'User');
            localStorage.setItem('teams_user_email', email);
            
            // Redirect to home
            navigate('/');
        }, 1000);
    };

    const handleGuestLogin = () => {
        localStorage.setItem('teams_user_name', 'Guest User');
        navigate('/');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#464775] to-[#5b5fc7] flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-[#464775] rounded-full mb-4">
                        <div className="w-8 h-8 bg-white rounded"></div>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-800">Sign in to TeamsMeet</h1>
                    <p className="text-gray-600 mt-2">Enter your credentials to continue</p>
                </div>

                {/* Login Form */}
                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Email address
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                className="w-full pl-10 pr-3 py-3 border-2 border-gray-300 rounded-lg focus:border-[#464775] focus:ring-2 focus:ring-[#464775]/20 outline-none transition-all"
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Password
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                className="w-full pl-10 pr-10 py-3 border-2 border-gray-300 rounded-lg focus:border-[#464775] focus:ring-2 focus:ring-[#464775]/20 outline-none transition-all"
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <label className="flex items-center">
                            <input
                                type="checkbox"
                                className="w-4 h-4 text-[#464775] border-gray-300 rounded focus:ring-[#464775]"
                            />
                            <span className="ml-2 text-sm text-gray-600">Remember me</span>
                        </label>
                        <button type="button" className="text-sm text-[#464775] hover:underline">
                            Forgot password?
                        </button>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !email || !password}
                        className="w-full bg-[#464775] hover:bg-[#5b5fc7] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
                    >
                        <LogIn className="w-5 h-5" />
                        {loading ? 'Signing in...' : 'Sign in'}
                    </button>
                </form>

                {/* Divider */}
                <div className="flex items-center my-6">
                    <div className="flex-1 border-t border-gray-300"></div>
                    <span className="px-4 text-gray-500 text-sm">OR</span>
                    <div className="flex-1 border-t border-gray-300"></div>
                </div>

                {/* Guest Login */}
                <button
                    onClick={handleGuestLogin}
                    className="w-full bg-gray-100 hover:bg-gray-200 border border-gray-300 text-gray-800 font-medium py-3 px-6 rounded-lg transition-all"
                >
                    Continue as Guest
                </button>

                {/* Footer */}
                <div className="mt-8 text-center text-sm text-gray-600">
                    <p>By signing in, you agree to our</p>
                    <p>
                        <a href="#" className="text-[#464775] hover:underline">Terms of Service</a>
                        {' '}and{' '}
                        <a href="#" className="text-[#464775] hover:underline">Privacy Policy</a>
                    </p>
                </div>

                {/* Back to Home */}
                <button
                    onClick={() => navigate('/')}
                    className="w-full mt-4 text-gray-600 hover:text-gray-800 py-2"
                >
                    ← Back to Home
                </button>
            </div>
        </div>
    );
}