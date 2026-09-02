# Remote Repository Setup

Recommended initial visibility: private GitHub repository.

Public repository publication requires a separate disclosure review after source safety, history safety, evidence review and credential rotation.

Manual setup:

1. Create an empty GitHub repository.
2. Do not initialize it with a README when local files already exist.
3. Copy the HTTPS or SSH URL.
4. Add the remote:

```powershell
git remote add origin <REMOTE_URL>
```

5. Verify the remote:

```powershell
git remote -v
```

6. Push only after repository safety passes and the initial commit is reviewed:

```powershell
git push -u origin main
```

Do not put access tokens in remote URLs. Remote configuration is `manual-action-required` until an approved URL is supplied.
