module.exports = {
  apps: [
    {
      name: "cybercom-web",
      script: "npm",
      args: "run start --workspace=@cybercom/web -- --port 3000",
      cwd: "/var/www/cy-com.com",
      env: {
        NODE_ENV: "production"
      }
    },
    {
      name: "cybercom-portal",
      script: "npm",
      args: "run start --workspace=@cybercom/portal -- --port 3001",
      cwd: "/var/www/cy-com.com",
      env: {
        NODE_ENV: "production"
      }
    },
    {
      name: "cybercom-partners",
      script: "npm",
      args: "run start --workspace=@cybercom/partners -- --port 3002",
      cwd: "/var/www/cy-com.com",
      env: {
        NODE_ENV: "production"
      }
    },
    {
      name: "cybercom-docs",
      script: "npm",
      args: "run start --workspace=@cybercom/docs -- --port 3003",
      cwd: "/var/www/cy-com.com",
      env: {
        NODE_ENV: "production"
      }
    }
  ]
};
