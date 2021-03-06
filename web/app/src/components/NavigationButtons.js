import React from 'react'

import { withRouter } from 'react-router-dom'
import styled from '@emotion/styled'

import { BottomNavigation, BottomNavigationAction } from '@mui/material'
import { Home, Receipt, AccountTree } from '@mui/icons-material'
import UnstyledLink from 'app/components/UnstyledLink'

const FullButton = ({ to, ...props }) => (
  <UnstyledLink style={{ minWidth: 85, flex: 1 }} to={to}>
    <BottomNavigationAction {...props} />
  </UnstyledLink>
)

const StyledNav = styled(BottomNavigation)`
  &&& {
    @media only screen and (max-width: 425px) {
      ${({ mobile }) => (!mobile ? 'display: none;' : '')}
      position: sticky;
      bottom: 0;
      left: 0;
      width: 100%;
    }

    @media only screen and (min-width: 426px) {
      ${({ mobile }) => (mobile ? 'display: none;' : '')}
    }
  }
`

const paths = ['/', '/blog', '/projects']
const NavigationButtons = ({ location, mobile }) => {
  const split = location.pathname.split('/')
  const menuIndex = split.length === 1 ? 0 : paths.indexOf('/' + split[1])

  return (
    <StyledNav showLabels value={menuIndex} mobile={mobile ? 'true' : null}>
      <FullButton label="Home" icon={<Home />} to={paths[0]} />
      <FullButton label="Blog" icon={<Receipt />} to={paths[1]} />
      <FullButton label="Projects" icon={<AccountTree />} to={paths[2]} />
    </StyledNav>
  )
}

export default withRouter(NavigationButtons)
