function wait(ms = 300) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function login(
  email: string,
  password: string,
): Promise<{ token: string }> {
  await wait()

  if (!email.trim() || !password.trim()) {
    throw new Error('이메일과 비밀번호를 모두 입력해 주세요.')
  }

  return {
    token: `mock-token-for-${email.trim().toLowerCase()}`,
  }
}
