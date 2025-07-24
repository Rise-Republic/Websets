import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '@/hooks/useAuth';

const schema = z
  .object({
    token: z.string().min(1, 'Token required'),
    newPassword: z.string().min(6, 'Password too short'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.newPassword === d.confirmPassword, {
    message: 'Passwords must match',
    path: ['confirmPassword'],
  });

type FormData = z.infer<typeof schema>;

const PasswordResetConfirmForm: React.FC = () => {
  const { confirmPasswordReset } = useAuth() as any;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    await confirmPasswordReset(data.token, data.newPassword);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="token">Token</label>
        <input id="token" {...register('token')} />
        {errors.token && <p>{errors.token.message}</p>}
      </div>
      <div>
        <label htmlFor="newPassword">New Password</label>
        <input id="newPassword" type="password" {...register('newPassword')} />
        {errors.newPassword && <p>{errors.newPassword.message}</p>}
      </div>
      <div>
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input id="confirmPassword" type="password" {...register('confirmPassword')} />
        {errors.confirmPassword && <p>{errors.confirmPassword.message}</p>}
      </div>
      <button type="submit">Reset Password</button>
    </form>
  );
};

export default PasswordResetConfirmForm;
