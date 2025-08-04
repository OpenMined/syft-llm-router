# Account Management User Flow

This document describes the updated frontend user flow for account creation and management.

## Overview

The frontend now includes a comprehensive account management system that handles:
1. Automatic account creation during onboarding
2. Account validation for existing users
3. Password updates for invalid credentials
4. Seamless integration with the onboarding process
5. Email auto-detection from SyftBox username API

## User Flow

### 1. Initial Onboarding

When a user first visits the application:

1. **Profile Selection**: User chooses between "Provider Mode" or "Client Mode"
2. **Automatic Account Setup**: 
   - System fetches user email from `/username` API
   - Attempts to create account automatically with animation
   - Shows connection progress with CTA
3. **Flow Branching**: Based on creation results:
   - **Success**: Account created, user proceeds to main application
   - **Account Exists (409)**: User is prompted for password
   - **Other Errors**: User is prompted to create account manually

### 2. Account Creation Flow

When creating a new account:

1. **Automatic Creation**: System automatically attempts to create account using email from `/username` API
2. **Visual Feedback**: Shows animated connection progress with explanatory CTA
3. **Response Handling**:
   - **Success**: Account created, user sees success animation and proceeds
   - **Account Exists (409)**: User is prompted to enter their password
4. **Password Update**: If account exists, user enters password via `/account/credential/update`

### 3. Password Update Flow

When credentials are invalid:

1. **Email Auto-Detection**: System gets email from `/username` API
2. **Password Update**: User enters new password via `/account/credential/update`
3. **Validation**: System validates the new credentials
4. **Success**: User proceeds to the main application

## API Endpoints

The frontend interacts with the following backend endpoints:

- `GET /username` - Get user email from SyftBox
- `GET /account/info` - Validate account connection
- `POST /account/credential/create` - Create new account
- `POST /account/credential/update` - Update account credentials
- `GET /account/url` - Get accounting service URL

## Components

### AccountModal
Handles the complete account creation and update flow with multiple steps:
- Account creation form
- Password input for existing accounts
- Success confirmation

### PasswordUpdateModal
Dedicated modal for updating invalid credentials with:
- Email display (non-editable)
- Password input
- Error handling



### OnboardingModal
Updated to include automatic account creation with animation and CTA integration.

## Error Handling

The system handles various error scenarios:

- **409 Conflict**: Account already exists, prompt for password
- **403 Forbidden**: Invalid credentials, prompt for password update (with auto-detected email)
- **404 Not Found**: No account exists, prompt for account creation
- **Network Errors**: Display user-friendly error messages with retry options

## State Management

Account state is managed through:
- Local component state for modal visibility
- API responses for account validation
- localStorage for profile persistence

## Security Considerations

- Passwords are never stored in localStorage
- All sensitive operations use HTTPS
- Error messages don't expose sensitive information
- Account validation happens on every app load 