import SvgIcon from './SvgIcon'

function IconLink({ href, icon, label, iconType = 'svg', iconClassName = 'button-icon' }) {
  return (
    <li>
      <a href={href} target="_blank">
        {iconType === 'svg' ? (
          <SvgIcon href={icon} />
        ) : (
          <img className={iconClassName} src={icon} alt="" />
        )}
        {label}
      </a>
    </li>
  )
}

export default IconLink
