import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from '@/hooks/useAuth';

const schema = z.object({ email: z.string().email('Invalid email') });

type FormData = z.infer<typeof schema>;

const PasswordResetRequestForm: React.FC = () => {
  const { requestPasswordReset } = useAuth() as any;
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    await requestPasswordReset(data.email);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} />
        {errors.email && <p>{errors.email.message}</p>}
      </div>
      <button type="submit">Send reset link</button>
    </form>
  );
};

export default PasswordResetRequestForm;
